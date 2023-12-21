variable "name" {
  type        = string
  description = "Name of the IAM role"
}

variable "lab_bucket_arn" {
  type        = string
  description = "ARN of the bucket where students can store their states"
}

variable "pass_students_policy_arn" {
  type        = string
  description = "ARN of the policy used to grade students work"
}