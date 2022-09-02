resource "aws_sns_topic" "topic" {
  name = var.topic_name
}

resource "aws_sns_topic_subscription" "topic_lambda" {
  topic_arn = aws_sns_topic.topic.arn
  protocol  = "lambda"
  endpoint  = var.lambda_arn
}

resource "aws_lambda_permission" "with_sns" {
    statement_id = "AllowExecutionFromSNS"
    action = "lambda:InvokeFunction"
    function_name = var.lambda_arn
    principal = "sns.amazonaws.com"
    source_arn = aws_sns_topic.topic.arn
}
