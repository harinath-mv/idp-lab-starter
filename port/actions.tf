# Shared value: the GitHub Ocean integration all actions run through (found on Day 14)
locals {
  github_installation_id = "github-ocean"
}

# Day 14: a button on every GitHub repo entity that runs .github/workflows/port-hello.yml
resource "port_action" "say_hello" {
  identifier = "say_hello"
  title      = "Say hello (Day 14)"
  icon       = "Github"

  self_service_trigger = {
    operation            = "DAY-2"
    blueprint_identifier = "githubRepository"
    user_properties = {
      string_props = {
        message = {
          title    = "Message"
          required = true
          default  = "Hello from Port"
        }
      }
    }
  }

  integration_method = {
    installation_id         = local.github_installation_id
    integration_action_type = "dispatch_workflow"
    integration_action_execution_properties = {
      org                    = "harinath-mv"
      repo                   = "idp-lab-starter"
      workflow               = "port-hello.yml"
      report_workflow_status = "true"
      workflow_inputs = jsonencode({
        message = "{{ .inputs.message }}"
        entity  = "{{ .entity.identifier }}"
        run_id  = "{{ .run.id }}"
      })
    }
  }
}

# Day 16: a self-service action that reports live progress back to Port
resource "port_action" "repo_health_check" {
  identifier  = "repo_health_check"
  title       = "Repo health check (Day 16)"
  icon        = "Github"
  description = "Counts open, merged and stale PRs and reports the result here"

  self_service_trigger = {
    operation            = "DAY-2"
    blueprint_identifier = "githubRepository"
    user_properties = {
      number_props = {
        days = {
          title    = "Look back (days)"
          required = true
          default  = 7
          minimum  = 1
          maximum  = 90
        }
      }
    }
  }

  integration_method = {
    installation_id         = local.github_installation_id
    integration_action_type = "dispatch_workflow"
    integration_action_execution_properties = {
      org                    = "harinath-mv"
      repo                   = "idp-lab-starter"
      workflow               = "repo-health.yml"
      report_workflow_status = "true"
      workflow_inputs = jsonencode({
        days   = "{{ .inputs.days }}"
        entity = "{{ .entity.identifier }}"
        run_id = "{{ .run.id }}"
      })
    }
  }
}

# Day 17: developers request a bucket; the platform builds it with Terraform
resource "port_action" "create_s3_bucket" {
  identifier  = "create_s3_bucket"
  title       = "Create S3 bucket"
  icon        = "AWS"
  description = "Get a secure, versioned S3 bucket in dev or prod, built by the platform Terraform module"

  self_service_trigger = {
    operation            = "CREATE"
    blueprint_identifier = port_blueprint.s3_bucket.identifier
    user_properties = {
      string_props = {
        purpose = {
          title       = "Purpose"
          description = "3-20 lowercase letters, numbers or dashes, e.g. orders-data"
          required    = true
          pattern     = "^[a-z0-9-]{3,20}$"
        }
        environment = {
          title    = "Environment"
          required = true
          enum     = ["dev", "prod"]
          default  = "dev"
        }
      }
    }
    order_properties = ["purpose", "environment"]
  }

  integration_method = {
    installation_id         = local.github_installation_id
    integration_action_type = "dispatch_workflow"
    integration_action_execution_properties = {
      org                    = "harinath-mv"
      repo                   = "idp-lab-starter"
      workflow               = "create-s3-bucket.yml"
      report_workflow_status = "true"
      workflow_inputs = jsonencode({
        purpose      = "{{ .inputs.purpose }}"
        env          = "{{ .inputs.environment }}"
        requested_by = "{{ .trigger.by.user.email }}"
        run_id       = "{{ .run.id }}"
      })
    }
  }
}
