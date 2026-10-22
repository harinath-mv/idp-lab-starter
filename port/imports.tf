# The sample data already created these 3 blueprints in Port.
# These blocks tell Terraform: "they exist, take them over" instead of creating new ones.
import {
  to = port_blueprint.environment
  id = "environment"
}

import {
  to = port_blueprint.service
  id = "service"
}

import {
  to = port_blueprint.deployment
  id = "deployment"
}