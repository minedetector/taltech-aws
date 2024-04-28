variable "uni_id" {
  type        = string
  description = "Students Uni-id aka unique identification code"
  default     = "salli"
}

variable "vpc_id" {
  type = string
  description = "ID of main VPC"
  default = "vpc-0864ffadf65555894"
}