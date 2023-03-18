variable "name" {
  type        = string
  description = "Name of the subnet"
}

variable "vpc_id" {
  type        = string
  description = "ID of the VPC that the subnet will be attached to"
}

variable "cidr_block" {
  type        = string
  description = "CIDR block to be used by the subnet"
}

variable "routes" {
  type = map(object({
    cidr_block = string
    gateway_id = string
  }))
  default = {}
}

variable "subnet_type" {
  type        = string
  description = "The type of subnet that will be created, i.e public or private"
}

variable "public_ip_by_default" {
  default     = false
  type        = bool
  description = "Whether or not the instances created in the subnet should have a public IP address by default"
}