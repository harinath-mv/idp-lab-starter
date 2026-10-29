# who can do what in Port, defined as code.
#
# Roles in Port:  Admin  = platform team (builds the portal)
#                 Member = developers (use the portal)
#
# Rule of thumb: developers USE actions; they do not hand-edit what the platform owns.

# 1. "Create S3 bucket" (Day 17 action): every developer can run it.
resource "port_action_permissions" "create_s3_bucket" {
  action_identifier = port_action.create_s3_bucket.identifier
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

# 2. New action: a developer asks to change a service's criticality.
#    No GitHub, no code: Port updates the catalog itself (upsert entity),
#    but only after a platform Admin approves it.
resource "port_action" "change_service_criticality" {
  identifier        = "change_service_criticality"
  title             = "Change service criticality"
  icon              = "Alert"
  description       = "Ask the platform team to change how critical a service is (needs approval)"
  required_approval = "true"

  self_service_trigger = {
    operation            = "DAY-2"
    blueprint_identifier = port_blueprint.service.identifier
    user_properties = {
      string_props = {
        criticality = {
          title    = "New criticality"
          required = true
          enum     = ["low", "medium", "high", "critical"]
          enum_colors = {
            low      = "turquoise"
            medium   = "yellow"
            high     = "orange"
            critical = "red"
          }
        }
        reason = {
          title       = "Reason"
          description = "Why does this change? e.g. now handles customer payments"
          required    = true
          min_length  = 10
        }
      }
    }
    order_properties = ["criticality", "reason"]
  }

  upsert_entity_method = {
    blueprint_identifier = port_blueprint.service.identifier
    mapping = {
      identifier = "{{ .entity.identifier }}"
      properties = jsonencode({
        criticality = "{{ .inputs.criticality }}"
      })
    }
  }
}

resource "port_action_permissions" "change_service_criticality" {
  action_identifier = port_action.change_service_criticality.identifier
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

# 3. S3 Bucket entities are created only by the self-service flow.
#    Developers can SEE them, but cannot add, delete or edit them by hand.
resource "port_blueprint_permissions" "s3_bucket" {
  blueprint_identifier = port_blueprint.s3_bucket.identifier
  entities = {
    register   = { roles = ["Admin"], users = [], teams = [] }
    unregister = { roles = ["Admin"], users = [], teams = [] }
    update     = { roles = ["Admin"], users = [], teams = [] }
    update_metadata_properties = {
      icon       = { roles = ["Admin"], users = [], teams = [] }
      identifier = { roles = ["Admin"], users = [], teams = [] }
      team       = { roles = ["Admin"], users = [], teams = [] }
      title      = { roles = ["Admin"], users = [], teams = [] }
    }
  }
}