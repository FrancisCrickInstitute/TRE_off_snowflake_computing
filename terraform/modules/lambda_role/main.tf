resource aws_iam_role lambda {
  name               = "lambda-role"
  assume_role_policy = <<EOF
{
   "Version": "2012-10-17",
   "Statement": [
       {
           "Action": "sts:AssumeRole",
           "Principal": {
               "Service": "lambda.amazonaws.com"
           },
           "Effect": "Allow"
       }
   ]
}
 EOF
}

data aws_iam_policy_document lambda {
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
    actions   = ["s3:*"]
    effect    = "Allow"
    resources = ["arn:aws:s3:::*"]
  }
  statement {
    actions = [
      "events:PutTargets",
      "events:RemoveTargets",
      "events:PutRule",
      "events:DeleteRule"
    ]
    effect    = "Allow"
    resources = ["arn:aws:events:*"]
  }
  statement {
    actions   = ["secretsmanager:*"]
    effect    = "Allow"
    resources = ["arn:aws:secretsmanager:*"]
  }
  statement {
    actions = [
      "lambda:InvokeFunction",
      "lambda:GetFunction",
      "lambda:AddPermission",
      "lambda:RemovePermission"
    ]
    effect    = "Allow"
    resources = ["arn:aws:lambda:*"]
  }
  statement {
    actions = [
      "kms:*"
    ]
    effect    = "Allow"
    resources = ["*"]
  }
}

resource aws_iam_policy lambda {
  name   = "lambda-policy"
  path   = "/"
  policy = data.aws_iam_policy_document.lambda.json
}

resource "aws_iam_role_policy_attachment" "lambda" {
  policy_arn = aws_iam_policy.lambda.arn
  role       = aws_iam_role.lambda.name
}
