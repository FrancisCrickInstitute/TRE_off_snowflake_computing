resource "aws_cloudwatch_event_rule" "rule" {
    schedule_expression = var.rate
    is_enabled = var.is_enabled
}

resource "aws_cloudwatch_event_target" "target" {
    rule = aws_cloudwatch_event_rule.rule.name
    arn = var.lambda_arn
}

resource "aws_lambda_permission" "lambda_permission" {
    statement_id = "AllowExecutionFromCloudWatch"
    action = "lambda:InvokeFunction"
    function_name = var.lambda_name
    principal = "events.amazonaws.com"
    source_arn = aws_cloudwatch_event_rule.rule.arn
}