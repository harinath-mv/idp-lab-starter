provider "aws" {
  region = "ap-south-1"

  default_tags {
    tags = {
      project    = "idp-lab"
      env        = "prod"
      managed_by = "terraform"
    }
  }
}

module "app_bucket" {
  source  = "../../modules/s3-bucket"
  env     = "prod"
  purpose = "app-data"
}
