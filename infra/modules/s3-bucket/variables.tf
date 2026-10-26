variable "env" {
  description = "Environment name, for example dev or prod"
  type        = string
}

variable "purpose" {
  description = "What the bucket is for, for example app-data"
  type        = string
}

variable "force_destroy" {
  description = "Allow terraform destroy even when the bucket has files (lab only)"
  type        = bool
  default     = true
}
