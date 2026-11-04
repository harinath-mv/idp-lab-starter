# Day 20 (Part 2): "Register a service" - a developer adds a new service to the catalog with a form.
#
# Form features shown here:
#   pattern            -> the name must follow our naming rule
#   format = "team"    -> a dropdown of Port teams (Day 19)
#   enum + default     -> fixed choices with a sensible default
#   visible_jq_query   -> the README field appears only for high / critical services
# No GitHub and no code: Port creates the entity itself (upsert_entity_method).

resource "port_action" "register_service" {
  identifier  = "register_service"
  title       = "Register a service"
  icon        = "Microservice"
  description = "Add a new service to the catalog, owned by your team"

  self_service_trigger = {
    operation            = "CREATE"
    blueprint_identifier = port_blueprint.service.identifier
    user_properties = {
      string_props = {
        name = {
          title       = "Service name"
          description = "Lowercase letters, digits and dashes, 3-30 characters, e.g. refunds-api"
          required    = true
          pattern     = "^[a-z][a-z0-9-]{2,29}$"
        }
        team = {
          title    = "Owning team"
          format   = "team"
          required = true
        }
        language = {
          title    = "Language"
          required = true
          enum     = ["Python", "Node", "Java", "Go"]
        }
        criticality = {
          title    = "Criticality"
          required = true
          enum     = ["low", "medium", "high", "critical"]
          default  = "medium"
        }
        readme = {
          title            = "README link"
          description      = "Expected for high and critical services"
          format           = "url"
          visible_jq_query = ".form.criticality == \"high\" or .form.criticality == \"critical\""
        }
      }
    }
    order_properties = ["name", "team", "language", "criticality", "readme"]
  }

  upsert_entity_method = {
    blueprint_identifier = port_blueprint.service.identifier
    title                = "{{ .inputs.name }}"
    mapping = {
      identifier = "{{ .inputs.name }}"
      teams_jq   = "{{ .inputs.team }}"
      properties = jsonencode({
        language    = "{{ .inputs.language }}"
        criticality = "{{ .inputs.criticality }}"
        readme      = "{{ .inputs.readme }}"
      })
    }
  }
}

# Every developer may register a service; no approval needed (low risk, easy to undo).
resource "port_action_permissions" "register_service" {
  action_identifier = port_action.register_service.identifier
  permissions = {
    execute = {
      roles = ["Admin", "Member"]
      users = []
      teams = []
    }
    approve = {
      roles = ["Admin"]
      users = []
      teams = []
    }
  }
}
