# AWS Dev Container 
### by rUv

This repository provides a fully configured development environment optimized for working with AWS services, including serverless Lambda deployments, using GitHub Codespaces. It includes the AWS CLI, AWS SAM CLI, Boto3, and additional tools necessary for serverless development.

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
git clone https://github.com/ruvnet/your-repository.git
cd your-repository
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
```

### Step 4: Launch Codespace

1. Push your changes to GitHub:
   ```sh
   git add .devcontainer/
   git commit -m "Add dev container configuration with Boto3 and AWS SAM CLI"
   git push origin main
   ```

2. Go to your repository on GitHub.
3. Click on the green "Code" button and select "Open with Codespaces".
4. If you don't see the option, make sure you have access to GitHub Codespaces.

### Step 5: Verify Setup

Once the Codespace is up and running, verify the AWS CLI and SAM CLI installations by running:

```sh
aws --version
sam --version
```

### Example Project Structure

The repository includes an example serverless application structure to get you started.

```
.
├── .devcontainer
│   ├── devcontainer.json
│   └── Dockerfile
├── hello_world
│   ├── app.py
│   ├── requirements.txt
├── template.yaml
└── README.md
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
 