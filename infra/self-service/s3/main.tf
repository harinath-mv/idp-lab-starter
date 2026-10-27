terraform {
  required_version = ">= 1.10.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # key is passed at init time (-backend-config), so every request gets its own state file
  backend "s3" {
    bucket       = "idp-lab-tfstate-753654067992"
    region       = "ap-south-1"
    encrypt      = true
    use_lockfile = true
  }
}

variable "env" {
  description = "dev or prod"
  type        = string
  validation {
    condition     = contains(["dev", "prod"], var.env)
    error_message = "env must be dev or prod."
  }
}

variable "purpose" {
  description = "What the bucket is for, 3-20 lowercase letters, numbers or dashes"
  type        = string
  validation {
    condition     = can(regex("^[a-z0-9-]{3,20}$", var.purpose))
    error_message = "purpose must be 3-20 lowercase letters, numbers or dashes."
  }
}

variable "requested_by" {
  description = "Who asked for it (from Port)"
  type        = string
  default     = "unknown"
}

provider "aws" {
  region = "ap-south-1"

  default_tags {
    tags = {
      project      = "idp-lab"
      env          = var.env
      managed_by   = "terraform"
      created_via  = "port-self-service"
      requested_by = var.requested_by
    }
  }
}

module "bucket" {
  source  = "../../modules/s3-bucket"
  env     = var.env
  purpose = var.purpose
}

output "bucket_name" {
  value = module.bucket.bucket_name
}