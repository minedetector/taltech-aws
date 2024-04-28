module "requests_layer" {
  source = "../../modules/lambda-layer"

  name            = "requests-layer"
  sourcefile_path = "../../files/requests_layer.zip"
}