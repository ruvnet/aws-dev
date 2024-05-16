# Deployment Script README

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
- `vpc_id` (string, optional): The VPC ID for the Lambda function.
- `subnet_ids` (list of strings, optional): The subnet IDs for the Lambda function.
- `security_group_ids` (list of strings, optional): The security group IDs for the Lambda function.

#### Response

- `message` (string): Deployment status message.
- `image_uri` (string): URI of the Docker image in ECR.
- `lambda_arn` (string): ARN of the deployed Lambda function.

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

This detailed README provides usage instructions, API endpoints, and the deployment process for the script, ensuring clarity and ease of use.