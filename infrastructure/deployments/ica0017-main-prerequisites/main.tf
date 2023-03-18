module "requests_layer" {
  source = "../../modules/lambda-layer"

  name            = "request-layer"
  sourcefile_path = "../../files/requests_layer.zip"
}