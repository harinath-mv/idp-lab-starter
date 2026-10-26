provider "aws" {
  region = "ap-south-1"

  default_tags {
    tags = {
      project    = "idp-lab"
      env        = "dev"
      managed_by = "terraform"
      owner      = "hari"
    }
  }
}

module "app_bucket" {
  source     = "../../modules/s3-bucket"
  env        = "dev"
  purpose    = "app-data"
  versioning = false
}
