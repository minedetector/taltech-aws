terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "= 3.75.1"
    }
  }
  required_version = ">= 1.0.11"
}

provider "aws" {
  profile = "ica0017-admin"
  region  = "eu-north-1"
}