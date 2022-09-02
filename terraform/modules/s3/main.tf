resource "aws_s3_bucket" lambda {
  bucket = var.bucket
}

resource "aws_s3_bucket_server_side_encryption_configuration" "encryption" {
  bucket = aws_s3_bucket.lambda.bucket
  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.kms_key.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

resource "aws_kms_key" "kms_key" {
  deletion_window_in_days = 10
}


resource "aws_s3_bucket_acl" "lambda" {
  bucket = aws_s3_bucket.lambda.id
  acl    = "private"
}

resource "aws_s3_bucket_notification" lambda {
  bucket = aws_s3_bucket.lambda.id
  lambda_function {
    lambda_function_arn = var.lambda_arn
    events              = [
      "s3:ObjectCreated:*"
    ]
    filter_suffix = ".json"
  }
}

resource "aws_lambda_permission" lambda {
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_name
  principal     = "s3.amazonaws.com"
  source_arn    = "arn:aws:s3:::${aws_s3_bucket.lambda.id}"
}

data aws_iam_policy_document for_gateway {
  statement {
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    effect    = "Allow"
    resources = ["*"]
    sid       = "CreateCloudWatchLogs"
  }
  statement {
    actions   = ["s3:Put*"]
    effect    = "Allow"
    resources = [
      aws_s3_bucket.lambda.arn,
      "${aws_s3_bucket.lambda.arn}/*"
    ]
  }
}

resource aws_iam_policy for_gateway {
  name   = "gateway-policy-on-${var.bucket}"
  path   = "/"
  policy = data.aws_iam_policy_document.for_gateway.json
}

resource "aws_iam_role_policy_attachment" "lambda" {
  policy_arn = aws_iam_policy.for_gateway.arn
  role       = var.gateway_role
}


resource "aws_iam_group_policy_attachment" "group-attachment" {
  group      = var.group
  policy_arn = aws_iam_policy.for_gateway.arn
}