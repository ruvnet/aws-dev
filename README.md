```
        ____ ___       
_______|    |   ___  __
\_  __ |    |   \  \/ /
 |  | \|    |  / \   / 
 |__|  |______/   \_/  
                       
 Optimized VS Code and Code Spaces
```
# AWS Serverless Ai Dev Environment
This repository provides a fully configured development environment optimized for working with AWS services, including serverless Lambda deployments, using GitHub Codespaces. It includes the AWS CLI, AWS SAM CLI, Boto3, and additional tools necessary for serverless development.

Created by **Reuven Cohen (rUv)**, this environment is designed to streamline and optimize the deployment of AWS Lambda functions with optional VPC configurations.

## Purpose

The purpose of this repository is to provide a ready-to-use development setup that simplifies the process of developing, testing, and deploying serverless applications on AWS. By leveraging GitHub Codespaces and Docker, developers can ensure consistency across different development environments and accelerate their workflow.

## Features

- **AWS CLI**: Manage AWS services directly from the command line.
- **AWS SAM CLI**: Build, test, and deploy serverless applications.
- **Boto3**: Python SDK for AWS services.
- **Docker**: Containerize and manage your Lambda functions.
- **Pre-configured Environment**: Ready-to-use settings and dependencies.
- **Extensions**: Includes useful VS Code extensions for Docker, AWS Toolkit, and more.

## Prerequisites

Ensure you have the following:
- Access to GitHub Codespaces.
- AWS account and credentials.

## Getting Started

### Step 1: Clone the Repository

Clone this repository to your local machine:

```sh
git clone https://github.com/ruvnet/aws-dev.git
cd aws-dev
```

### Step 2: Configure AWS Credentials

Set up your AWS credentials as environment variables. Add the following lines to your `.bashrc`, `.bash_profile`, or `.zshrc`:

```sh
export AWS_ACCESS_KEY_ID=your_access_key_id
export AWS_SECRET_ACCESS_KEY=your_secret_access_key
export AWS_DEFAULT_REGION=us-east-1
```

After updating, source the file to apply the changes:

```sh
source ~/.bashrc
# or
source ~/.bash_profile
# or
source ~/.zshrc
```

### Step 3: Setup Dev Container

The repository includes a `.devcontainer` folder with the necessary configuration files.

#### .devcontainer/devcontainer.json
```json
{
  "name": "AWS Dev Container",
  "build": {
    "dockerfile": "Dockerfile",
    "context": "."
  },
  "settings": {
    "terminal.integrated.shell.linux": "/bin/bash",
    "python.pythonPath": "/workspaces/aws-dev/.venv/bin/python"
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
  "postCreateCommand": "python3 -m venv .venv && . .venv/bin/activate && pip install --upgrade pip && pip install -r deployment/requirements.txt -r hello_world/requirements.txt",
  "forwardPorts": [8000],
  "remoteUser": "vscode",
  "remoteEnv": {
    "AWS_ACCESS_KEY_ID": "${localEnv:AWS_ACCESS_KEY_ID}",
    "AWS_SECRET_ACCESS_KEY": "${localEnv:AWS_SECRET_ACCESS_KEY}",
    "AWS_DEFAULT_REGION": "${localEnv:AWS_DEFAULT_REGION}"
  }
}
```

#### .devcontainer/Dockerfile
```Dockerfile
# Base image
FROM mcr.microsoft.com/vscode/devcontainers/base:0-buster

# Install AWS CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install && \
    rm -rf awscliv2.zip ./aws

# Install system dependencies
RUN apt-get update && apt-get install -y \
    jq \
    python3 \
    python3-pip \
    python3-distutils \
    python3-venv \
    docker.io \
    build-essential \
    curl \
    sudo \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Manually install pip (if needed)
RUN curl -O https://bootstrap.pypa.io/get-pip.py && \
    python3 get-pip.py && \
    rm get-pip.py

# Install Rust (needed for maturin)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Install maturin with specific version and other dependencies
RUN pip install --upgrade pip && \
    pip install maturin==1.0.0 typing-extensions==4.6.3

# Install other Python dependencies
RUN pip install boto3 fastapi pydantic uvicorn

# Install AWS SAM CLI
RUN pip install aws-sam-cli

# Install GitHub CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg && \
    sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null && \
    sudo apt update && \
    sudo apt install -y gh

# Ensure pip is available globally
RUN ln -s /usr/bin/pip3 /usr/bin/pip

# Set the default shell to bash
SHELL ["/bin/bash", "-c"]

# Set user
USER vscode
```

### Step 4: Run the Deployment Script

1. **Start the FastAPI Server**:
    ```bash
    uvicorn deployment.deploy_script:app --reload
    ```

2. **Deploy via API Call**:
    Use a tool like `curl` or Postman to send a POST request to the `/deploy` endpoint with the required payload.

    Example payload:
    ```json
    {
        "repository_name": "my-repo",
        "image_tag": "latest",
        "python_script": "def lambda_handler(event, context): return {'statusCode': 200, 'body': 'Hello, World!'}",
        "requirements": "requests\n",
        "vpc_id": "vpc-12345678",
        "subnet_ids": ["subnet-12345678", "subnet-87654321"],
        "security_group_ids": ["sg-12345678"]
    }
    ```

### Example Project Structure

The repository includes an example serverless application structure to get you started.

```
.
.
├── .devcontainer
│   ├── devcontainer.json
│   └── Dockerfile
├── .gitignore
├── deployment
│   ├── deploy_script.py
│   ├── requirements.txt
├── hello_world
│   ├── app.py
│   ├── requirements.txt
├── scripts
│   ├── get-pip.py
│   ├── rust.sh
│   ├── setup.sh
├── template.yaml
└── README.md
```

#### deployment/deploy_script.py

```python
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
                'Subnet

Ids': request.subnet_ids or [],
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
```

#### deployment/requirements.txt

```txt
boto3
fastapi
pydantic
uvicorn
```

#### hello_world/app.py

```python
def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': 'Hello, World!'
    }
```

#### hello_world/requirements.txt

```txt
boto3
```

#### template.yaml

```yaml
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
```

## Additional Information

- **Environment Variables**: The dev container is configured to use your local environment variables for AWS credentials.
- **Custom Scripts**: You can add custom scripts and configurations as needed.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
 