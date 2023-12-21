variable "name" {
  type        = string
  description = "Name of the lambda function"
}

variable "pass_students_policy_arn" {
  type        = string
  description = "ARN of the policy used to grade students work"
}