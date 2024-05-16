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
  "postCreateCommand": "aws --version && sam --version",
  "forwardPorts": [3000],
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

# Install Boto3
RUN pip3 install boto3

# Install AWS SAM CLI
RUN pip3 install aws-sam-cli

# Set the default shell to bash
SHELL ["/bin/bash", "-c"]

# Set user
USER vscode
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
git add .devcontainer/ hello_world/ template.yaml
git commit -m "Add dev container configuration for serverless with Boto3 and AWS SAM CLI"
git push origin main

echo "Dev container configuration for serverless development complete."
