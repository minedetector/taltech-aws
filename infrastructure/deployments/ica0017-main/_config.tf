terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "= 4.64.0"
    }
  }
  required_version = ">= 1.0.11"

  backend "s3" {
    region = "eu-north-1"
    bucket = "ica0017-tf-state"
    key    = "ica0017.tfstate"
  }
}

provider "aws" {
  profile = "ica0017_test_students"
  region  = "eu-north-1"
}