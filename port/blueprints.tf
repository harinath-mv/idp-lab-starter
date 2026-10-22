resource "port_blueprint" "environment" {
  identifier = "environment"
  title      = "Environment"
  icon       = "Environment"

  properties = {
    string_props = {
      cloud = {
        title = "Cloud"
        enum  = ["AWS", "Azure"]
      }
      region = {
        title = "Region"
      }
      stage = {
        title    = "Stage"
        enum     = ["dev", "prod"]
        required = true
      }
    }
  }
}

resource "port_blueprint" "service" {
  identifier = "service"
  title      = "Service"
  icon       = "Microservice"

  properties = {
    string_props = {
      owner = {
        title = "Owner team"
      }
      language = {
        title = "Language"
        enum  = ["Python", "Node", "Java", "Go"]
      }
      readme = {
        title  = "README link"
        format = "url"
      }
    }
  }
}

resource "port_blueprint" "deployment" {
  identifier = "deployment"
  title      = "Deployment"
  icon       = "Deployment"

  properties = {
    string_props = {
      version = {
        title = "Version"
      }
      status = {
        title = "Status"
        enum  = ["Success", "Failed", "Running"]
      }
    }
  }

  relations = {
    service = {
      title    = "Service"
      target   = port_blueprint.service.identifier
      required = true
      many     = false
    }
    environment = {
      title    = "Environment"
      target   = port_blueprint.environment.identifier
      required = true
      many     = false
    }
  }
}
