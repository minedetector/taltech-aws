variable "name" {
  type        = string
  description = "Name of the test"
}

variable "source_file_path" {
  type        = string
  description = "Source of the code to test the lab"
}

variable "zip_file_path" {
  type        = string
  description = "Path to upload the zipped file to"
}

variable "role_arn" {
  type        = string
  description = "Arn of the IAM role"
}

variable "trigger_frequency" {
  type        = string
  description = "How often the lambda is triggered by a cloudwatch event"
  default = ""
}

variable "is_event_enabled" {
  type = bool
  default     = false
  description = "Whether or not the lambda function should be automatically triggered at the trigger_frequency"
}

variable "timeout" {
  default     = 120
  description = "How long the Lambda will run before erroring"
}

variable "memory_size" {
  default     = 128
  description = "How much memory is allocated to the lambda script"
}