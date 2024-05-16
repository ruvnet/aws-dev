import os
import subprocess
import boto3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI()

class DeployRequest(BaseModel):
    repository_name: str
    image_tag: str
    python_script: str
    requirements: str
    vpc_id: Optional[str] = None
    subnet_ids: Optional[List[str]] = None
    security_group_ids: Optional[List[str]] = None

@app.post("/deploy")
def deploy(request: DeployRequest):
    try:
        # Ensure Docker is running
        docker_running = subprocess.run(["docker", "info"], capture_output=True, text=True)
        if docker_running.returncode != 0:
            raise HTTPException(status_code=500, detail="Docker daemon is not running. Please start Docker daemon.")

        # Step 1: Create a virtual environment
        subprocess.run(["python3", "-m", "venv", "venv"], check=True)

        # Step 2: Write the Python script to a file
        with open("app.py", "w") as f:
            f.write(request.python_script)

        # Step 3: Write the requirements to a file
        with open("requirements.txt", "w") as f:
            f.write(request.requirements)

        # Step 4: Install dependencies
        subprocess.run(["venv/bin/pip", "install", "-r", "requirements.txt"], check=True)

        # Step 5: Create a Dockerfile
        dockerfile_content = f"""
        FROM public.ecr.aws/lambda/python:3.8
        COPY requirements.txt .
        RUN pip install -r requirements.txt
        COPY app.py .
        CMD ["app.lambda_handler"]
        """
        with open("Dockerfile", "w") as f:
            f.write(dockerfile_content)

        # Step 6: Build the Docker image
        image_name = f"{request.repository_name}:{request.image_tag}"
        build_result = subprocess.run(["docker", "build", "-t", image_name, "."], capture_output=True, text=True)

        if build_result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Docker build failed: {build_result.stderr}")

        # Step 7: Authenticate Docker to AWS ECR
        region = "us-west-2"  # Change to your desired region
        account_id = boto3.client('sts').get_caller_identity().get('Account')
        ecr_uri = f"{account_id}.dkr.ecr.{region}.amazonaws.com"
        login_command = f"aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin {ecr_uri}"
        login_result = subprocess.run([login_command], shell=True, capture_output=True, text=True)

        if login_result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Docker login failed: {login_result.stderr}")

        # Step 8: Create ECR repository if it doesn't exist
        ecr_client = boto3.client('ecr', region_name=region)
        try:
            ecr_client.create_repository(repositoryName=request.repository_name)
        except ecr_client.exceptions.RepositoryAlreadyExistsException:
            pass

        # Step 9: Tag and push the Docker image to ECR
        subprocess.run(["docker", "tag", image_name, f"{ecr_uri}/{image_name}"], check=True)
        subprocess.run(["docker", "push", f"{ecr_uri}/{image_name}"], check=True)

        # Step 10: Create or update the Lambda function
        lambda_client = boto3.client('lambda', region_name=region)
        function_name = "my-lambda-function"
        try:
            response = lambda_client.create_function(
                FunctionName=function_name,
                Role=f"arn:aws:iam::{account_id}:role/lambda-execution-role",
                Code={
                    'ImageUri': f"{ecr_uri}/{image_name}"
                },
                PackageType='Image',
                Publish=True,
                VpcConfig={
                    'SubnetIds': request.subnet_ids or [],
                    'SecurityGroupIds': request.security_group_ids or []
                } if request.vpc_id else {}
            )
        except lambda_client.exceptions.ResourceConflictException:
            response = lambda_client.update_function_code(
                FunctionName=function_name,
                ImageUri=f"{ecr_uri}/{image_name}",
                Publish=True
            )
            if request.vpc_id:
                lambda_client.update_function_configuration(
                    FunctionName=function_name,
                    VpcConfig={
                        'SubnetIds': request.subnet_ids or [],
                        'SecurityGroupIds': request.security_group_ids or []
                    }
                )

        return {"message": "Deployment successful", "image_uri": f"{ecr_uri}/{image_name}", "lambda_arn": response['FunctionArn']}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
