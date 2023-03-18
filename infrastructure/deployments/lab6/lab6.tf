terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.27"
    }
  }
  backend "s3" {
    region = "eu-north-1"
    bucket = "ica0017-lab6-states"
    key    = "ica0017-savisaar.tfstate"
  }

  required_version = ">= 1.3.7"
}

provider "aws" {
  profile = "ica0017_test_students"
  region  = "eu-north-1"
}

data "template_file" "this" {
  template = file("init_script.sh")

  vars = {
    uni_id = var.uni_id
  }
}

resource "aws_instance" "web" {
  ami           = "ami-08c308b1bb265e927"
  instance_type = "t3.micro"

  subnet_id = "subnet-098b2ee2b4fc6d33c"

  vpc_security_group_ids = [
    "${aws_security_group.allow_ssh_and_http.id}"
  ]

  user_data = data.template_file.this.rendered

  key_name = "larasi-personal-mac"

  tags = {
    Name = "${var.uni_id}-tf",
    User = "${var.uni_id}"
  }
}

resource "aws_security_group" "allow_ssh_and_http" {
  name        = "${var.uni_id}-allow-ssh-and-http"
  description = "Allow ssh and http connections"
  vpc_id      = "vpc-0864ffadf65555894"

  ingress {
    description = "Allow http"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.uni_id}-webserver-tf",
    User = "${var.uni_id}"
  }
}
