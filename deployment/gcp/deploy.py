import os
import subprocess
import json
from fastapi import FastAPI, HTTPException, File, UploadFile, APIRouter
from pydantic import BaseModel
from typing import Optional, List
from google.auth import default
from google.auth.transport.requests import Request
from google.cloud import storage, functions_v1, container_v1, iam, pubsub_v1, monitoring_v3, billing_v1, logging_v2

app = FastAPI()
router = APIRouter()
misc_router = APIRouter()
bedrock_router = APIRouter()
iam_router = APIRouter()

class DeployRequest(BaseModel):
    repository_name: str
    image_tag: str
    python_script: str
    requirements: str
    function_name: str
    region: Optional[str] = None
    vpc_id: Optional[str] = None
    subnet_ids: Optional[List[str]] = None
    security_group_ids: Optional[List[str]] = None

class AdvancedDeployRequest(BaseModel):
    repository_name: str
    image_tag: str
    base_image: str
    build_commands: List[str]
    function_name: str
    region: Optional[str] = None
    vpc_id: Optional[str] = None
    subnet_ids: Optional[List[str]] = None
    security_group_ids: Optional[List[str]] = None

class VpcConfig(BaseModel):
    vpc_id: str
    subnet_ids: List[str]
    security_group_ids: List[str]

class FunctionConfig(BaseModel):
    repository_name: str
    image_tag: str
    function_name_prefix: str
    number_of_functions: int
    vpc_id: str
    subnet_ids: List[str]
    security_group_ids: List[str]
    region: Optional[str] = None 
    log_retention_days: Optional[int] = 7

class InvokeConfig(BaseModel):
    function_name_prefix: str
    number_of_functions: int
    payload: dict
    region: Optional[str] = None

class TimePeriod(BaseModel):
    Start: str
    End: str

class BudgetRequest(BaseModel):
    AccountId: str
    BudgetName: str

class UpdateFunctionConfig(BaseModel):
    function_name: str
    memory_size: Optional[int] = None
    timeout: Optional[int] = None
    environment_variables: Optional[dict] = None
    region: Optional[str] = None

class BedrockModelRequest(BaseModel):
    prompt: str
    max_tokens_to_sample: Optional[int] = 300
    temperature: Optional[float] = 0.1
    top_p: Optional[float] = 0.9

class IAMUserRequest(BaseModel):
    user_name: str

class IAMRoleRequest(BaseModel):
    role_name: str
    assume_role_policy_document: dict

class IAMPolicyRequest(BaseModel):
    policy_name: str
    policy_document: dict

class AssumeRoleRequest(BaseModel):
    role_arn: str
    role_session_name: str

class AccessKeyRequest(BaseModel):
    user_name: str

# Deployment endpoints
@app.post("/deploy")
async def deploy(request: DeployRequest):
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
        FROM python:3.8-slim
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

        # Step 7: Authenticate Docker to Google Container Registry (GCR)
        subprocess.run(["gcloud", "auth", "configure-docker"], check=True)

        # Step 8: Tag and push the Docker image to GCR
        gcr_uri = f"gcr.io/{request.repository_name}/{image_name}"
        subprocess.run(["docker", "tag", image_name, gcr_uri], check=True)
        subprocess.run(["docker", "push", gcr_uri], check=True)

        # Step 9: Deploy the function to Google Cloud Functions
        gcloud_command = [
            "gcloud", "functions", "deploy", request.function_name,
            "--region", request.region or "us-central1",
            "--runtime", "python38",
            "--trigger-http",
            "--allow-unauthenticated",
            "--source", ".",
            "--entry-point", "lambda_handler",
            "--set-env-vars", "requirements.txt"
        ]
        subprocess.run(gcloud_command, check=True)

        return {"message": "Deployment successful", "image_uri": gcr_uri}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/advanced-deploy")
async def advanced_deploy(request: AdvancedDeployRequest, files: List[UploadFile] = File(...)):
    try:
        # Ensure Docker is running
        docker_running = subprocess.run(["docker", "info"], capture_output=True, text=True)
        if docker_running.returncode != 0:
            raise HTTPException(status_code=500, detail="Docker daemon is not running. Please start Docker daemon.")

        # Save uploaded files
        for file in files:
            file_location = f"./{file.filename}"
            with open(file_location, "wb+") as file_object:
                file_object.write(file.file.read())

        # Create Dockerfile with advanced options
        dockerfile_content = f"""
        FROM {request.base_image}
        """
        for command in request.build_commands:
            dockerfile_content += f"\nRUN {command}"
        dockerfile_content += "\nCOPY . ."
        dockerfile_content += '\nCMD ["app.lambda_handler"]'

        with open("Dockerfile", "w") as f:
            f.write(dockerfile_content)

        # Build the Docker image
        image_name = f"{request.repository_name}:{request.image_tag}"
        build_result = subprocess.run(["docker", "build", "-t", image_name, "."], capture_output=True, text=True)

        if build_result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Docker build failed: {build_result.stderr}")

        # Authenticate Docker to Google Container Registry (GCR)
        subprocess.run(["gcloud", "auth", "configure-docker"], check=True)

        # Tag and push the Docker image to GCR
        gcr_uri = f"gcr.io/{request.repository_name}/{image_name}"
        subprocess.run(["docker", "tag", image_name, gcr_uri], check=True)
        subprocess.run(["docker", "push", gcr_uri], check=True)

        # Deploy the function to Google Cloud Functions
        gcloud_command = [
            "gcloud", "functions", "deploy", request.function_name,
            "--region", request.region or "us-central1",
            "--runtime", "python38",
            "--trigger-http",
            "--allow-unauthenticated",
            "--source", ".",
            "--entry-point", "lambda_handler",
            "--set-env-vars", "requirements.txt"
        ]
        subprocess.run(gcloud_command, check=True)

        return {"message": "Advanced deployment successful", "image_uri": gcr_uri}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/deploy-multiple-functions")
async def deploy_multiple_functions(config: FunctionConfig):
    try:
        # Authenticate Docker to Google Container Registry (GCR)
        subprocess.run(["gcloud", "auth", "configure-docker"], check=True)

        # Ensure Google Cloud Container Repository exists
        gcr_uri = f"gcr.io/{config.repository_name}"
        for i in range(config.number_of_functions):
            function_name = f"{config.function_name_prefix}-{i}"
            image_name = f"{config.repository_name}:{config.image_tag}"

            # Tag and push the Docker image to GCR
            subprocess.run(["docker", "tag", image_name, f"{gcr_uri}/{image_name}"], check=True)
            subprocess.run(["docker", "push", f"{gcr_uri}/{image_name}"], check=True)

            # Deploy the function to Google Cloud Functions
            gcloud_command = [
                "gcloud", "functions", "deploy", function_name,
                "--region", config.region or "us-central1",
                "--runtime", "python38",
                "--trigger-http",
                "--allow-unauthenticated",
                "--source", ".",
                "--entry-point", "lambda_handler",
                "--set-env-vars", "requirements.txt"
            ]
            subprocess.run(gcloud_command, check=True)

        return {"message": f"Deployed {config.number_of_functions} functions successfully"}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/invoke-cloud-function")
async def invoke_cloud_function(function_name: str, region: Optional[str] = None):
    try:
        # Initialize Google Cloud Functions client
        client = functions_v1.CloudFunctionsServiceClient()

        # Get the function URI
        function_path = client.function_path(os.getenv("GOOGLE_CLOUD_PROJECT"), region or "us-central1", function_name)
        function = client.get_function(request={"name": function_path})
        function_uri = function.https_trigger.url

        # Invoke the Cloud Function
        response = requests.post(function_uri)

        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/invoke-multiple-functions")
async def invoke_multiple_functions(config: InvokeConfig):
    try:
        responses = []
        for i in range(config.number_of_functions):
            function_name = f"{config.function_name_prefix}-{i}"
            response = await invoke_cloud_function(function_name, config.region)
            responses.append(response)

        return {"message": f"Invoked {config.number_of_functions} functions successfully", "responses": responses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/list-cloud-functions")
async def list_cloud_functions(region: Optional[str] = None):
    try:
        # Initialize Google Cloud Functions client
        client = functions_v1.CloudFunctionsServiceClient()
        parent = f"projects/{os.getenv('GOOGLE_CLOUD_PROJECT')}/locations/{region or 'us-central1'}"

        # List Cloud Functions
        functions = client.list_functions(request={"parent": parent})
        function_names = [func.name for func in functions]

        return {"functions": function_names}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/delete-cloud-function")
async def delete_cloud_function(function_name: str, region: Optional[str] = None):
    try:
        # Initialize Google Cloud Functions client
        client = functions_v1.CloudFunctionsServiceClient()
        function_path = client.function_path(os.getenv("GOOGLE_CLOUD_PROJECT"), region or "us-central1", function_name)

        # Delete the Cloud Function
        client.delete_function(request={"name": function_path})

        return {"message": f"Cloud function {function_name} deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/list-gcr-repositories")
async def list_gcr_repositories():
    try:
        # Initialize Google Cloud Container Registry client
        client = container_v1.ContainerAnalysisClient()
        parent = f"projects/{os.getenv('GOOGLE_CLOUD_PROJECT')}/locations/-/repositories"

        # List GCR repositories
        repositories = client.list_repositories(request={"parent": parent})
        repository_names = [repo.name for repo in repositories]

        return {"repositories": repository_names}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/delete-gcr-repository")
async def delete_gcr_repository(repository_name: str):
    try:
        # Initialize Google Cloud Container Registry client
        client = container_v1.ContainerAnalysisClient()
        repository_path = client.repository_path(os.getenv("GOOGLE_CLOUD_PROJECT"), "-", repository_name)

        # Delete the GCR repository
        client.delete_repository(request={"name": repository_path})

        return {"message": f"GCR repository {repository_name} deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/set-vpc-config")
async def set_vpc_config(vpc_config: VpcConfig):
    try:
        # Here you would typically store the VPC config in a database or use it directly
        # For demonstration, we just return the config
        return {"message": "VPC configuration set successfully", "vpc_config": vpc_config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/edit-vpc-config")
async def edit_vpc_config(vpc_config: VpcConfig):
    try:
        # Here you would typically update the VPC config in a database or use it directly
        # For demonstration, we just return the config
        return {"message": "VPC configuration updated successfully", "vpc_config": vpc_config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-vpc-config")
async def get_vpc_config():
    try:
        # Here you would typically retrieve the VPC config from a database
        # For demonstration, we just return a mock config
        mock_vpc_config = {
            "vpc_id": "vpc-12345678",
            "subnet_ids": ["subnet-12345678", "subnet-87654321"],
            "security_group_ids": ["sg-12345678", "sg-87654321"]
        }
        return {"vpc_config": mock_vpc_config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/get-cost-and-usage")
async def get_cost_and_usage(time_period: TimePeriod, metrics: List[str] = ["cost"], granularity: str = "MONTHLY"):
    try:
        client = billing_v1.CloudBillingClient()
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        response = client.get_billing_account(request={"name": f"projects/{project_id}"})
        return response['account_budget']
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/describe-budget")
async def describe_budget(budget_request: BudgetRequest):
    try:
        client = billing_v1.CloudBillingClient()
        budget_name = f"billingAccounts/{budget_request.AccountId}/budgets/{budget_request.BudgetName}"
        response = client.get_budget(request={"name": budget_name})
        return response['budget_amount']
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/describe-report-definitions")
async def describe_report_definitions():
    try:
        client = billing_v1.CloudBillingClient()
        response = client.list_report_definitions()
        return response['report_definitions']
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/get-products")
async def get_products(service_code: str, filters: List[dict]):
    try:
        client = billing_v1.CloudBillingClient()
        response = client.list_services(request={"filter": {"service": service_code}})
        return response['services']
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Assuming the cost optimization hub API is available
@router.post("/get-savings-plans-coverage")
async def get_savings_plans_coverage(time_period: TimePeriod):
    try:
        client = billing_v1.CloudBillingClient()
        response = client.get_cost_and_usage(request={
            "timePeriod": {
                'start': time_period.Start,
                'end': time_period.End
            }
        })
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# Include the router in the FastAPI app instance
app.include_router(router, prefix="/costs", tags=["Costs"])

@router.get("/function-status/{function_name}")
async def function_status(function_name: str, region: Optional[str] = None):
    try:
        region = region or os.getenv("GOOGLE_CLOUD_PROJECT")
        client = functions_v1.CloudFunctionsServiceClient()
        function_path = client.function_path(region, region or "us-central1", function_name)
        response = client.get_function(request={"name": function_path})
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/update-function-configuration")
async def update_function_configuration(config: UpdateFunctionConfig):
    try:
        client = functions_v1.CloudFunctionsServiceClient()
        function_path = client.function_path(os.getenv("GOOGLE_CLOUD_PROJECT"), config.region or "us-central1", config.function_name)

        update_params = {
            "name": function_path,
            "memory": config.memory_size,
            "timeout": config.timeout,
            "environment_variables": config.environment_variables
        }

        response = client.update_function(request=update_params)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list-cloud-logging-metrics/{function_name}")
async def list_cloud_logging_metrics(function_name: str, region: Optional[str] = None):
    try:
        client = logging_v2.LoggingServiceV2Client()
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        response = client.list_log_entries(request={
            "resource_names": [f"projects/{project_id}"],
            "filter": f"resource.type=\"cloud_function\" AND resource.labels.function_name=\"{function_name}\""
        })
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list-cloud-logs/{function_name}")
async def list_cloud_logs(function_name: str, region: Optional[str] = None):
    try:
        client = logging_v2.LoggingServiceV2Client()
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        response = client.list_log_entries(request={
            "resource_names": [f"projects/{project_id}"],
            "filter": f"resource.type=\"cloud_function\" AND resource.labels.function_name=\"{function_name}\""
        })
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get-function-errors/{function_name}")
async def get_function_errors(function_name: str, region: Optional[str] = None):
    try:
        client = logging_v2.LoggingServiceV2Client()
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        response = client.list_log_entries(request={
            "resource_names": [f"projects/{project_id}"],
            "filter": f"resource.type=\"cloud_function\" AND resource.labels.function_name=\"{function_name}\" AND severity=\"ERROR\""
        })
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list-all-functions")
async def list_all_functions(region: Optional[str] = None):
    try:
        client = functions_v1.CloudFunctionsServiceClient()
        parent = f"projects/{os.getenv('GOOGLE_CLOUD_PROJECT')}/locations/{region or 'us-central1'}"
        functions = client.list_functions(request={"parent": parent})
        function_names = [func.name for func in functions]
        return {"functions": function_names}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(router, prefix="/management", tags=["Management"])

@misc_router.get("/regions")
async def list_regions():
    try:
        # List Google Cloud regions
        regions = ["us-central1", "us-east1", "us-east4", "us-west1", "us-west2", "us-west3", "us-west4"]
        return {"regions": regions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(misc_router, prefix="/misc", tags=["Misc"])

@bedrock_router.get("/list-foundation-models")
async def list_foundation_models(region: Optional[str] = None):
    try:
        # Example placeholder for listing foundation models
        models = ["gpt-3", "bert", "t5"]
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@bedrock_router.post("/invoke-model")
async def invoke_model(model_request: BedrockModelRequest, model_id: str, region: Optional[str] = None):
    try:
        # Example placeholder for invoking a foundation model
        response = {
            "model_id": model_id,
            "prompt": model_request.prompt,
            "response": "This is a generated response from the model."
        }
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(bedrock_router, prefix="/bedrock", tags=["Bedrock"])

@iam_router.post("/create-user")
async def create_user(request: IAMUserRequest):
    try:
        client = iam.IAMClient()
        response = client.create_service_account(request={"account_id": request.user_name, "service_account": {}})
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@iam_router.get("/list-users")
async def list_users():
    try:
        client = iam.IAMClient()
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        response = client.list_service_accounts(request={"name": f"projects/{project_id}"})
        users = response.accounts
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@iam_router.post("/create-role")
async def create_role(request: IAMRoleRequest):
    try:
        client = iam.IAMClient()
        response = client.create_role(request={"role_id": request.role_name, "role": {}})
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@iam_router.post("/attach-policy-to-role")
async def attach_policy_to_role(role_name: str, policy_arn: str):
    try:
        client = iam.IAMClient()
        role_path = client.role_path(os.getenv("GOOGLE_CLOUD_PROJECT"), role_name)
        response = client.set_iam_policy(request={"resource": role_path, "policy": {"bindings": [{"role": policy_arn, "members": []}]}})
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@iam_router.post("/create-policy")
async def create_policy(request: IAMPolicyRequest):
    try:
        client = iam.IAMClient()
        response = client.create_policy(request={"policy": {"name": request.policy_name, "bindings": [{"role": request.policy_document}]}})
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@iam_router.post("/assume-role")
async def assume_role(request: AssumeRoleRequest):
    try:
        # Example placeholder for assuming a role
        response = {"assumed_role": request.role_arn}
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@iam_router.post("/create-access-key")
async def create_access_key(request: AccessKeyRequest):
    try:
        client = iam.IAMClient()
        response = client.create_service_account_key(request={"name": f"projects/-/serviceAccounts/{request.user_name}"})
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(iam_router, prefix="/iam", tags=["IAM"])

# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
