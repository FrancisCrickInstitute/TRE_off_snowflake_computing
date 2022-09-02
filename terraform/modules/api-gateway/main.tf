# Create API Gateway Role
resource "aws_iam_role" "s3_api_gateway_role" {
  name = "s3-api-gateway-role"

  # Create Trust Policy for API Gateway
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "apigateway.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
  EOF
}

data aws_iam_policy_document s3_encryption {
  statement {
    actions = [
      "kms:GenerateDataKey"
    ]
    effect    = "Allow"
    resources = ["*"]
  }
}

resource aws_iam_policy s3_encryption {
  name   = "gateway_s3_encryption_policy"
  path   = "/"
  policy = data.aws_iam_policy_document.s3_encryption.json
}

resource "aws_iam_role_policy_attachment" "lambda" {
  policy_arn = aws_iam_policy.s3_encryption.arn
  role       = aws_iam_role.s3_api_gateway_role.name
}

resource "aws_api_gateway_stage" "s3_proxy" {
  stage_name    = var.env
  rest_api_id   = aws_api_gateway_rest_api.s3_proxy.id
  deployment_id = aws_api_gateway_deployment.s3_proxy.id
}

resource "aws_api_gateway_deployment" "s3_proxy" {
  rest_api_id = aws_api_gateway_rest_api.s3_proxy.id
}

resource "aws_api_gateway_rest_api" "s3_proxy" {
  name        = "s3"
  description = "API for s3 integration"
}

resource "aws_api_gateway_resource" "bucket" {
  rest_api_id = aws_api_gateway_rest_api.s3_proxy.id
  parent_id   = aws_api_gateway_rest_api.s3_proxy.root_resource_id
  path_part   = "{bucket}"
}

resource "aws_api_gateway_resource" "item" {
  rest_api_id = aws_api_gateway_rest_api.s3_proxy.id
  parent_id   = aws_api_gateway_resource.bucket.id
  path_part   = "{item}"
}

resource "aws_api_gateway_method" "put_in_bucket" {
  rest_api_id   = aws_api_gateway_rest_api.s3_proxy.id
  resource_id   = aws_api_gateway_resource.item.id
  http_method   = "PUT"
  authorization = "AWS_IAM"

  request_parameters = {
    "method.request.path.bucket" = true
    "method.request.path.item"   = true
  }
}

resource "aws_api_gateway_integration" "s3_integration" {
  rest_api_id = aws_api_gateway_rest_api.s3_proxy.id
  resource_id = aws_api_gateway_resource.item.id
  http_method = aws_api_gateway_method.put_in_bucket.http_method

  # Included because of this issue: https://github.com/hashicorp/terraform/issues/10501
  integration_http_method = "PUT"
  type                    = "AWS"

  # See uri description: https://docs.aws.amazon.com/apigateway/api-reference/resource/integration/
  uri         = "arn:aws:apigateway:${var.region}:s3:path/{bucket}/{item}"
  credentials = aws_iam_role.s3_api_gateway_role.arn

  request_parameters = {
    "integration.request.path.bucket" = "method.request.path.bucket"
    "integration.request.path.item"   = "method.request.path.item"
  }
}

resource "aws_api_gateway_method_response" "response_200" {
  rest_api_id = aws_api_gateway_rest_api.s3_proxy.id
  resource_id = aws_api_gateway_resource.item.id
  http_method = aws_api_gateway_method.put_in_bucket.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Timestamp"      = true
    "method.response.header.Content-Length" = true
    "method.response.header.Content-Type"   = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method_response" "response_400" {
  rest_api_id = aws_api_gateway_rest_api.s3_proxy.id
  resource_id = aws_api_gateway_resource.item.id
  http_method = aws_api_gateway_method.put_in_bucket.http_method
  status_code = "400"
}

resource "aws_api_gateway_method_response" "response_500" {
  rest_api_id = aws_api_gateway_rest_api.s3_proxy.id
  resource_id = aws_api_gateway_resource.item.id
  http_method = aws_api_gateway_method.put_in_bucket.http_method
  status_code = "500"
}

resource "aws_api_gateway_integration_response" "integration_response_200" {
  rest_api_id = aws_api_gateway_rest_api.s3_proxy.id
  resource_id = aws_api_gateway_resource.item.id
  http_method = aws_api_gateway_method.put_in_bucket.http_method
  status_code = aws_api_gateway_method_response.response_200.status_code

  response_parameters = {
    "method.response.header.Timestamp"      = "integration.response.header.Date"
    "method.response.header.Content-Length" = "integration.response.header.Content-Length"
    "method.response.header.Content-Type"   = "integration.response.header.Content-Type"
  }
}

resource "aws_api_gateway_integration_response" "integration_response_400" {
  rest_api_id = aws_api_gateway_rest_api.s3_proxy.id
  resource_id = aws_api_gateway_resource.item.id
  http_method = aws_api_gateway_method.put_in_bucket.http_method
  status_code = aws_api_gateway_method_response.response_400.status_code

  selection_pattern = "4\\d{2}"
}

resource "aws_api_gateway_integration_response" "integration_response_500" {
  rest_api_id = aws_api_gateway_rest_api.s3_proxy.id
  resource_id = aws_api_gateway_resource.item.id
  http_method = aws_api_gateway_method.put_in_bucket.http_method
  status_code = aws_api_gateway_method_response.response_500.status_code

  selection_pattern = "5\\d{2}"
}

resource "aws_api_gateway_deployment" "s3_proxy_deployment" {
  rest_api_id = aws_api_gateway_rest_api.s3_proxy.id
}