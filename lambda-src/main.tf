provider "aws" {
  # region can be omitted if set via environment variables or AWS CLI config
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
      Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"  # Add this line
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
  image_uri     = "637304539725.dkr.ecr.us-east-1.amazonaws.com/lambda-bedrock:latest"
  role          = aws_iam_role.lambda_exec_role.arn

  timeout     = 30
  memory_size = 512
}

resource "aws_lambda_function_url" "bedrock_api_url" {
  function_name     = aws_lambda_function.bedrock_api.function_name
  authorization_type = "NONE"
}

output "lambda_function_url" {
  value = aws_lambda_function_url.bedrock_api_url.function_url
}
