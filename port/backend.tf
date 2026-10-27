terraform {
  backend "s3" {
    bucket       = "idp-lab-tfstate-753654067992"
    key          = "port/terraform.tfstate"
    region       = "ap-south-1"
    use_lockfile = true
    encrypt      = true
  }
}