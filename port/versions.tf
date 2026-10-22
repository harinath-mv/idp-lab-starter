terraform {
  required_version = ">= 1.10.0"

  required_providers {
    port = {
      source  = "port-labs/port-labs"
      version = "~> 2.30"
    }
  }
}

# Credentials come from environment variables PORT_CLIENT_ID and PORT_CLIENT_SECRET
provider "port" {
  base_url = "https://api.port.io" # EU region (app.port.io)
}
