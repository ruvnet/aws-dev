
#!/bin/bash

# Create .devcontainer directory
mkdir -p .devcontainer

# Create devcontainer.json
cat <<EOL > .devcontainer/devcontainer.json
{
  "name": "AWS Dev Container",
  "build": {
    "dockerfile": "Dockerfile",
    "context": "."
  },
  "settings": {
    "terminal.integrated.shell.linux": "/bin/bash"
  },
  "extensions": [
    "amazonwebservices.aws-toolkit-vscode",
    "kddejong.vscode-cfn-lint",
    "redhat.vscode-yaml",
    "hashicorp.terraform",
    "ms-python.python",
    "ms-azuretools.vscode-docker",
    "amazonwebservices.aws-sam-cli-toolkit"
  ],
  "postCreateCommand": "aws --version && sam --version && gh --version",
  "forwardPorts": [8000],
  "remoteUser": "vscode",
  "remoteEnv": {
    "AWS_ACCESS_KEY_ID": "\${localEnv:AWS_ACCESS_KEY_ID}",
    "AWS_SECRET_ACCESS_KEY": "\${localEnv:AWS_SECRET_ACCESS_KEY}",
    "AWS_DEFAULT_REGION": "\${localEnv:AWS_DEFAULT_REGION}"
  }
}
EOL

# Create Dockerfile
cat <<EOL > .devcontainer/Dockerfile
# Base image
FROM mcr.microsoft.com/vscode/devcontainers/base:0-buster

# Install AWS CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    sudo ./aws/install && \
    rm -rf awscliv2.zip ./aws

# Install other dependencies if needed
RUN apt-get update && apt-get install -y \
    jq \
    python3 \
    python3-pip \
    docker.io \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Install Boto3 and FastAPI dependencies
RUN pip3 install boto3 fastapi pydantic uvicorn

# Install AWS SAM CLI
RUN pip3 install aws-sam-cli

# Install GitHub CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg && \
    sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null && \
    sudo apt update && \
    sudo apt install -y gh

# Set the default shell to bash
SHELL ["/bin/bash", "-c"]

# Set user
USER vscode
EOL

# Create deployment directory
mkdir -p deployment

# Create deployment/deploy_script.py
cat <<EOL > deployment/deploy_script.py
import os
import subprocess
import boto3
from fastapi import FastAPI
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
    # Step 1: Create a virtual environment
    os.system("python3 -m venv venv")
    os.system("source venv/bin/activate")
    
    # Step 2: Write the Python script to a file
    with open("app.py", "w") as f:
        f.write(request.python_script)
    
    # Step 3: Write the requirements to a file
    with open("requirements.txt", "w") as f:
        f.write(request.requirements)
    
    # Step 4: Install dependencies
    os.system("venv/bin/pip install -r requirements.txt")
    
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
    os.system(f"docker build -t {image_name} .")
    
    # Step 7: Authenticate Docker to AWS ECR
    region = "us-west-2"  # Change to your desired region
    account_id = boto3.client('sts').get_caller_identity().get('Account')
    ecr_uri = f"{account_id}.dkr.ecr.{region}.amazonaws.com"
    os.system(f"aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin {ecr_uri}")
    
    # Step 8: Create ECR repository if it doesn't exist
    ecr_client = boto3.client('ecr', region_name=region)
    try:
        ecr_client.create_repository(repositoryName=request.repository_name)
    except ecr_client.exceptions.RepositoryAlreadyExistsException:
        pass
    
    # Step 9: Tag and push the Docker image to ECR
    os.system(f"docker tag {image_name} {ecr_uri}/{image_name}")
    os.system(f"docker push {ecr_uri}/{image_name}")
    
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

# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOL

# Create deployment/requirements.txt
cat <<EOL > deployment/requirements.txt
boto3
fastapi
pydantic
uvicorn
EOL

# Create example project structure
mkdir -p hello_world
cat <<EOL > hello_world/app.py
def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': 'Hello, World!'
    }
EOL

cat <<EOL > hello_world/requirements.txt
boto3
EOL

cat <<EOL > template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Resources:
  HelloWorldFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: app.lambda_handler
      Runtime: python3.8
      CodeUri: hello_world/
      Description: A simple Hello World function.
      MemorySize: 128
      Timeout: 3
      Policies:
        - AWSLambdaBasicExecutionRole
EOL

# Commit and push changes
git add .devcontainer/ deployment/ hello_world/ template.yaml
git commit -m "Add dev container configuration for serverless with Boto3, AWS SAM CLI, and GitHub CLI"
git push origin main

echo "Dev container configuration for serverless development complete."