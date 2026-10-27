# Day 17-B: "Create S3 bucket" as a Port Workflow (shows on the Self-Service Hub).
# Same GitHub workflow and Terraform module as the Day 17 action; only the front door is new.
#
#   [Form: purpose + environment]  --->  [Run create-s3-bucket.yml in GitHub]
#        node "trigger"                        node "run_github"

resource "port_workflow" "create_s3_bucket" {
  identifier  = "create-s3-bucket-wf"
  title       = "Create S3 bucket"
  description = "Get a secure, versioned S3 bucket in dev or prod, built by the platform Terraform module"
  icon        = "AWS"
  category    = "Platform actions" # becomes a section on the Self-Service Hub

  # Node 1: the form the developer fills in
  node {
    identifier = "trigger"
    title      = "Bucket request"

    self_serve_trigger {
      published                  = true
      action_card_button_text    = "Request"
      execute_action_button_text = "Create bucket"

      user_inputs {
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
    }
  }

  # Node 2: start the same GitHub workflow the Day 17 action uses
  node {
    identifier = "run_github"
    title      = "Build with Terraform"

    integration_action {
      installation_id             = local.github_installation_id # "github-ocean", from actions.tf
      integration_provider        = "github-ocean"
      integration_invocation_type = "dispatch_workflow"
      execution_properties = jsonencode({
        org      = "harinath-mv"
        repo     = "idp-lab-starter"
        workflow = "create-s3-bucket.yml"
        workflowInputs = {
          purpose = "{{ .outputs.trigger.purpose }}"
          env     = "{{ .outputs.trigger.environment }}"
        }
        reportWorkflowStatus = true
      })
    }
  }

  # The arrow between the two boxes
  connections {
    source_identifier = "trigger"
    target_identifier = "run_github"
  }
}
