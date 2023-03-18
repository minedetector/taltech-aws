variable "name" {
  type        = string
  description = "Name of the VPC"
}

variable "cidr_block" {
  type        = string
  description = "CIDR block for the VPC"
}

variable "create_igw" {
  type        = bool
  description = "whether or not the VPC should have a internet gateway"
}