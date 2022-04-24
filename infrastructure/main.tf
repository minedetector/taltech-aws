locals {
  lambda_zip_location  = "files/instanceStopFunction.zip"
  lambda_code_location = "files/instanceStopFunction.py"
}

data "archive_file" "lambda" {
  type        = "zip"
  source_file = local.lambda_code_location
  output_path = local.lambda_zip_location
}

resource "aws_cloudwatch_event_rule" "every_hour" {
  name                = "every-hour"
  description         = "Fires every hour"
  schedule_expression = "rate(1 hour)"
}

resource "aws_cloudwatch_event_target" "this" {
  rule      = aws_cloudwatch_event_rule.every_hour.name
  target_id = "lambda"
  arn       = aws_lambda_function.this.arn
}

resource "aws_lambda_permission" "this" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.every_hour.arn
}

resource "aws_lambda_function" "this" {
  filename      = "files/instanceStopFunction.zip"
  function_name = "stop_instance_after_hour"
  role          = aws_iam_role.iam_for_lambda.arn
  handler       = "instanceStopFunction.lambda_handler"

  timeout = 15
  runtime = "python3.9"
}