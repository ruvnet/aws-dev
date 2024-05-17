# Serverless Swarm Deployment System
## AWS Lambda Ai Agent Deployment Script 

## Introduction

Welcome to the Serverless Swarm Deployment System, a powerful and flexible solution for deploying, managing, and scaling Python applications on AWS Lambda using Docker containers. This system is designed to handle both simple and complex deployment scenarios, providing a seamless experience for developers and DevOps teams.

### Key Features

1. **Automated Deployment**: Easily deploy Python applications to AWS Lambda with minimal configuration. The system automates the creation of virtual environments, dependency installation, Docker image building, and pushing to AWS Elastic Container Registry (ECR).

2. **Multi-Function Deployment**: Deploy multiple Lambda functions simultaneously, making it ideal for large-scale applications or microservices architectures.

3. **Advanced Deployment Options**: Customize your deployments with advanced Docker build options, including the ability to specify base images, build commands, and more.

4. **Flexible Configuration**: Support for VPC configurations, security group settings, and subnet specifications ensures secure and optimized network configurations for your Lambda functions.

5. **Monitoring and Logging**: Integrated with AWS CloudWatch for capturing logs and metrics, enabling you to monitor the performance and health of your Lambda functions.

6. **Cost Management**: Utilize AWS Cost Explorer and Budget APIs to track and manage your AWS costs effectively.

7. **Error Handling and Alerts**: Incorporate AWS SNS or SQS for error handling and alerting, ensuring you are promptly notified of any issues.

8. **Permissions and Security**: Easily manage IAM policies and roles for your Lambda functions, ensuring appropriate access control and security.

9. **Regional Deployments**: Deploy functions across multiple AWS regions, providing flexibility and resilience for your applications.

10. **User-Friendly API**: A comprehensive set of API endpoints allows for easy integration and automation of deployment processes.

### Use Cases

- **Microservices**: Deploy and manage a swarm of microservices, each running as an independent Lambda function.
- **Batch Processing**: Execute large-scale batch processing tasks by deploying multiple Lambda functions that process data in parallel.
- **Event-Driven Architectures**: Build event-driven systems that respond to various triggers and events, scaling automatically based on demand.
- **Cost Optimization**: Track and manage AWS costs, ensuring efficient usage of resources and budget adherence.

### Getting Started

To get started with the Serverless Swarm Deployment System, follow the detailed instructions in the usage section of this README. The provided API endpoints allow you to deploy, manage, and monitor your Lambda functions with ease.

Whether you're building a complex serverless architecture or simply deploying a few Lambda functions, the Serverless Swarm Deployment System offers the tools and flexibility you need to succeed.

## Usage

This script is used to deploy a Python application to AWS Lambda using Docker containers. The deployment process involves creating a virtual environment, installing dependencies, building a Docker image, and pushing the image to AWS Elastic Container Registry (ECR). The script also creates or updates an AWS Lambda function using the Docker image.

### Running the Script

1. Ensure you have the necessary AWS credentials configured.
2. Start the FastAPI application:

   ```bash
   uvicorn deployment.deploy_script:app --host 0.0.0.0 --port 8000
   ```

3. Send a POST request to the `/deploy` endpoint with the required payload.

### Example Payload

```json
{
  "repository_name": "my-ecr-repository",
  "image_tag": "latest",
  "python_script": "def lambda_handler(event, context): return {'statusCode': 200, 'body': 'Hello, world!'}",
  "requirements": "boto3\nfastapi\npydantic",
  "vpc_id": "vpc-0bb1c79de3EXAMPLE",
  "subnet_ids": ["subnet-085deabcd12345678"],
  "security_group_ids": ["sg-0a123b456c789d012"]
}
```

## API Endpoints

### POST /deploy

Deploys the provided Python script to AWS Lambda using Docker.

#### Request Body

- `repository_name` (string): The name of the ECR repository.
- `image_tag` (string): The tag for the Docker image.
- `python_script` (string): The Python script to deploy.
- `requirements` (string): The requirements for the Python script.
- `function_name` (string): The name for the Lambda function.
- `region` (string, optional): The AWS region to deploy the function.
- `vpc_id` (string, optional): The VPC ID for the Lambda function.
- `subnet_ids` (list of strings, optional): The subnet IDs for the Lambda function.
- `security_group_ids` (list of strings, optional): The security group IDs for the Lambda function.

#### Response

- `message` (string): Deployment status message.
- `image_uri` (string): URI of the Docker image in ECR.
- `lambda_arn` (string): ARN of the deployed Lambda function.

### POST /advanced-deploy

Deploys a Python application to AWS Lambda with advanced Docker build options.

### POST /deploy-multiple-functions

Deploys multiple Lambda functions using Docker containers.

### POST /invoke-multiple-functions

Invokes multiple Lambda functions with the given payload.

### GET /invoke-lambda

Invokes a specific Lambda function and returns the response.

### GET /list-lambda-functions

Lists all Lambda functions in a specified region or across all regions if no region is specified.

### GET /list-all-functions

Lists all Lambda functions across all regions.

### DELETE /delete-lambda-function

Deletes a specified Lambda function.

### GET /list-ecr-repositories

Lists all ECR repositories in a specified region.

### DELETE /delete-ecr-repository

Deletes a specified ECR repository.

### POST /set-vpc-config

Sets the VPC configuration for a Lambda function.

### PUT /edit-vpc-config

Edits the VPC configuration for a Lambda function.

### GET /get-vpc-config

Retrieves the VPC configuration for a Lambda function.

### GET /regions

Lists all available AWS regions.

### POST /get-cost-and-usage

Retrieves cost and usage information from AWS Cost Explorer.

### POST /describe-budget

Describes an AWS budget.

### GET /describe-report-definitions

Describes all report definitions from AWS Cost and Usage Reports.

### POST /get-products

Retrieves AWS pricing information.

### POST /get-savings-plans-coverage

Retrieves coverage information for AWS Savings Plans.

### GET /function-status/{function_name}

Retrieves the status of a specified Lambda function.

### PUT /update-function-configuration

Updates the configuration of a specified Lambda function.

### GET /list-cloudwatch-metrics/{function_name}

Lists CloudWatch metrics for a specified Lambda function.

### GET /list-cloudwatch-logs/{function_name}

Lists CloudWatch logs for a specified Lambda function.

### GET /get-function-errors/{function_name}

Retrieves error logs for a specified Lambda function from CloudWatch.

## Deployment Process

1. **Create a Virtual Environment:**
   - A virtual environment is created using `python3 -m venv venv`.
   - The virtual environment is activated using `source venv/bin/activate`.

2. **Write the Python Script to a File:**
   - The provided Python script is written to `app.py`.

3. **Write the Requirements to a File:**
   - The provided requirements are written to `requirements.txt`.

4. **Install Dependencies:**
   - Dependencies are installed using `venv/bin/pip install -r requirements.txt`.

5. **Create a Dockerfile:**
   - A Dockerfile is created with the necessary instructions to build the Docker image.

6. **Build the Docker Image:**
   - The Docker image is built using `docker build -t <image_name> .`.

7. **Authenticate Docker to AWS ECR:**
   - Docker is authenticated to AWS ECR using `aws ecr get-login-password`.

8. **Create ECR Repository (if not exists):**
   - The ECR repository is created using the AWS SDK if it does not already exist.

9. **Tag and Push the Docker Image to ECR:**
   - The Docker image is tagged and pushed to ECR.

10. **Create or Update the Lambda Function:**
    - The Lambda function is created or updated with the new Docker image.
    - If a VPC ID is provided, the Lambda function is configured with the specified VPC settings.

### Example Commands

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Write script and requirements to files
echo "def lambda_handler(event, context): return {'statusCode': 200, 'body': 'Hello, world!'}" > app.py
echo "boto3\nfastapi\npydantic" > requirements.txt

# Install dependencies
venv/bin/pip install -r requirements.txt

# Create Dockerfile
echo "FROM public.ecr.aws/lambda/python:3.8\nCOPY requirements.txt .\nRUN pip install -r requirements.txt\nCOPY app.py .\nCMD [\"app.lambda_handler\"]" > Dockerfile

# Build Docker image
docker build -t my-ecr-repository:latest .

# Authenticate Docker to AWS ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin <account_id>.dkr.ecr.us-west-2.amazonaws.com

# Push Docker image to ECR
docker tag my-ecr-repository:latest <account_id>.dkr.ecr.us-west-2.amazonaws.com/my-ecr-repository:latest
docker push <account_id>.dkr.ecr.us-west-2.amazonaws.com/my-ecr-repository:latest

# Deploy Lambda function using the image from ECR
aws lambda create-function --function-name my-lambda-function --package-type Image --code ImageUri=<account_id>.dkr.ecr.us-west-2.amazonaws.com/my-ecr-repository:latest --role arn:aws:iam::<account_id>:role/lambda-execution-role
```
 