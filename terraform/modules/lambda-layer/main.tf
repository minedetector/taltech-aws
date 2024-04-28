resource "aws_lambda_layer_version" "this" {
  filename   = var.sourcefile_path
  layer_name = var.name

  compatible_runtimes = ["python3.9"]
  source_code_hash = filebase64sha256(var.sourcefile_path)
}