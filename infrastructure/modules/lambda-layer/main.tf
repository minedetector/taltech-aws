resource "aws_lambda_layer_version" "this" {
  filename   = var.sourcefile_path
  layer_name = var.name

  compatible_runtimes = ["python3.9"]
}