# Stock Query AI Agent – Serverless Bedrock FastAPI Solution

## Overview

This project is a serverless AI agent solution on AWS that provides a FastAPI endpoint for retrieving real-time and historical stock prices, powered by AWS Bedrock and orchestrated with a ReAct-type agent. It includes a modern React frontend (ChatGPT-style) for user interaction.

---

## Features

- **Serverless backend**: AWS Lambda (container image), Bedrock, FastAPI, Terraform
- **Agent orchestration**: Uses langgraph (ReAct agent)
- **Two tools**:
  - `retrieve_realtime_stock_price`
  - `retrieve_historical_stock_price`
- **Streaming responses**: Supports streaming back responses to the frontend
- **Frontend**: React single-page app (ChatGPT-style UI)
- **Infrastructure as Code**: All AWS resources provisioned via Terraform

---

## Architecture

```
[User] <---> [React Frontend] <---> [FastAPI on Lambda (Bedrock, Langgraph)] <---> [AWS Bedrock]
```

---

## Prerequisites

- AWS Account with Bedrock access (enable Bedrock and the desired model in the AWS Console)
- AWS CLI configured (`aws configure`)
- Docker installed (for building Lambda container)
- Terraform installed (for infrastructure)
- Python 3.8+ (for local testing)
- Node.js & npm (for frontend)

---

## Backend: FastAPI + Lambda + Bedrock

### 1. Clone the Repository

```bash
git clone https://github.com/BhavishyaTatineni/stock_query_agent
cd lambda-src
```

### 2. Local Development (Optional)

```bash
pip install -r requirements.txt
python app.py
```
- The API will be available at `http://localhost:8000/query`

### 3. Build and Push Docker Image to ECR (Use EC2 Amazon Linux)

1. **Create ECR repository:**
   ```bash
   aws ecr create-repository --repository-name lambda-bedrock --region us-east-1
   ```
2. **Authenticate Docker to ECR:**
   ```bash
   aws ecr get-login-password --region us-east-1 | \
   docker login --username AWS --password-stdin <your-account-id>.dkr.ecr.us-east-1.amazonaws.com
   ```
3. **Build Docker image:**
   ```bash
   docker build -t lambda-bedrock .
   ```
4. **Tag and push image:**
   ```bash
   docker tag lambda-bedrock:latest <your-account-id>.dkr.ecr.us-east-1.amazonaws.com/lambda-bedrock:latest
   docker push <your-account-id>.dkr.ecr.us-east-1.amazonaws.com/lambda-bedrock:latest
   ```

### 4. Deploy Infrastructure with Terraform

1. **Edit `main.tf`** (see below for a minimal example).
2. **Initialize and apply:**
   ```bash
   terraform init
   terraform apply
   ```
   - Type `yes` to confirm.

#### Example `main.tf` for Lambda Container + Bedrock + Lambda Function URL

```hcl
provider "aws" {
  region = "us-east-1"
}

resource "aws_iam_role" "lambda_exec_role" {
  name = "lambda_exec_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "bedrock_policy" {
  name = "BedrockAccessPolicy"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect   = "Allow"
      Action   = [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ]
      Resource = "*"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "attach_bedrock" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.bedrock_policy.arn
}

resource "aws_lambda_function" "bedrock_api" {
  function_name = "bedrock-api-lambda"
  package_type  = "Image"
  image_uri     = "<your-account-id>.dkr.ecr.us-east-1.amazonaws.com/lambda-bedrock:latest"
  role          = aws_iam_role.lambda_exec_role.arn
  timeout       = 30
  memory_size   = 512
}

resource "aws_lambda_function_url" "bedrock_api_url" {
  function_name      = aws_lambda_function.bedrock_api.function_name
  authorization_type = "NONE"
}

output "lambda_function_url" {
  value = aws_lambda_function_url.bedrock_api_url.function_url
}
```

### 5. Get Your Lambda HTTPS URL

After `terraform apply`, Terraform will output:
```
lambda_function_url = https://xxxx.lambda-url.us-east-1.on.aws/
```
Use this as your API endpoint in the frontend.

---

## Frontend: React Chat UI

### 1. Setup

```bash
cd ../stock-chat
npm install
```

### 2. Configure API Endpoint

- Edit `src/App.js` and set:
  ```js
  const API_URL = "https://xxxx.lambda-url.us-east-1.on.aws/query";
  ```

### 3. Run Locally

```bash
npm start
```
- The app will be available at `http://localhost:3000`

### 4. (Optional) Host on EC2

- You can use `serve` or Nginx to serve the built frontend:
  ```bash
  npm run build
  npx serve -s build
  ```

---

## User Acceptance Criteria

- **Source code** is in this repository with this README.
- **Infrastructure** is fully automated via Terraform.
- **Users** can interact with the UI, ask for real-time or historical stock prices, and see streamed responses.
- **No login/signup** required; single-page ChatGPT-style UI.

---

## Notes

- **Bedrock**: Enable Bedrock and the desired model in the AWS Console before deploying.
- **IAM**: The Lambda execution role must have both `bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream` permissions.
- **No S3 needed**: All code and dependencies are bundled in the Docker image.
- **Streaming**: The backend supports streaming responses to the frontend.
- **Extensible**: You can add more tools or models as needed.

---

## Troubleshooting

- **IAM errors**: Ensure no duplicate resource names in Terraform and that the policy includes all required Bedrock actions.
- **500 errors**: Usually indicate missing Bedrock permissions or model access.
- **EntityAlreadyExists**: Import the existing resource into Terraform or delete it manually.

---

## License

MIT

---

**Questions or issues? Open an issue or discussion in this repository!** 
