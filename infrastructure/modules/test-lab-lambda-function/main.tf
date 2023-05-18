data "archive_file" "lambda" {
  type        = "zip"
  output_path = var.zip_file_path

  source {
    content  = file(var.source_file_path)
    filename = "lambda_function.py"
  }
  source {
    content  = file("../../files/passed.txt")
    filename = "passed.txt"
  }
}

data "aws_lambda_layer_version" "this" {
  layer_name = "requests-layer"
}

resource "aws_cloudwatch_event_rule" "this" {
  name                = "${var.name}-event"
  description         = "Trigger the cloudwatch event for ${var.name} with the following ${var.trigger_frequency}"
  schedule_expression = var.trigger_frequency
  is_enabled          = var.is_event_enabled
}

resource "aws_cloudwatch_event_target" "this" {
  rule      = aws_cloudwatch_event_rule.this.name
  target_id = "lambda"
  arn       = aws_lambda_function.this.arn
}

resource "aws_lambda_permission" "this" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.this.arn
}

resource "aws_lambda_function" "this" {
  filename      = var.zip_file_path
  function_name = var.name
  role          = var.role_arn
  handler       = "lambda_function.lambda_handler"
  layers        = [data.aws_lambda_layer_version.this.arn]

  timeout = 60
  runtime = "python3.9"
}