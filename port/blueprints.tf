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

  # Added by the GitHub Ocean integration (23 Oct); adopted into code on Day 14.
  ownership = {
    type = "Direct"
  }

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
      criticality = {
        title       = "Criticality"
        description = "Service criticality level"
        icon        = "Alert"
        enum        = ["low", "medium", "high", "critical"]
        enum_colors = {
          low      = "turquoise"
          medium   = "yellow"
          high     = "orange"
          critical = "red"
        }
      }
    }
  }

  # Fields copied from the linked GitHub repository (used by the Day 12 mapping and scorecards).
  mirror_properties = {
    github_codeowners     = { path = "github_repository.codeowners", title = "Code Owners" }
    github_default_branch = { path = "github_repository.defaultBranch", title = "Default Branch" }
    github_description    = { path = "github_repository.description", title = "Description" }
    github_gitignore      = { path = "github_repository.gitignore", title = "Git Ignore" }
    github_language       = { path = "github_repository.language", title = "Programming Language" }
    github_last_push      = { path = "github_repository.last_push", title = "Last Repository Push" }
    github_pr_template    = { path = "github_repository.pr_template", title = "PR Template" }
    github_readme         = { path = "github_repository.readme", title = "README" }
    github_repository_id  = { path = "github_repository.$identifier", title = "Repo ID" }
    github_url            = { path = "github_repository.url", title = "Repository URL" }
    github_visibility     = { path = "github_repository.visibility", title = "Visibility" }
  }

  # DORA / engineering-health formulas added by the integration.
  calculation_properties = {
    deploy_freq_tier = {
      title       = "Deployment Frequency"
      description = "DORA deployment frequency tier (from production deployments)"
      icon        = "DefaultProperty"
      type        = "string"
      calculation = "if (.properties.total_deployments == null or .properties.total_deployments == 0) then \"Low\" else if (.properties.deployment_frequency // 0) >= 7 then \"Elite\" elif (.properties.deployment_frequency // 0) >= 1 then \"High\" elif (.properties.deployment_frequency // 0) >= 0.25 then \"Medium\" else \"Low\" end end"
      colorized   = true
      colors = {
        Elite  = "lime"
        High   = "blue"
        Medium = "orange"
        Low    = "red"
      }
    }
    github_cycle_time_trend = {
      title       = "PR Cycle Time Trend"
      description = "Weekly vs monthly PR cycle time"
      icon        = "DefaultProperty"
      type        = "string"
      calculation = "((.properties.github_pr_cycle_time // 0) - (.properties.github_pr_cycle_time_weekly // 0)) as $diff | if $diff > 0 then \"Improving\" elif $diff < 0 then \"Degrading\" else \"Stable\" end"
      colorized   = true
      colors = {
        Improving = "green"
        Stable    = "blue"
        Degrading = "red"
      }
    }
    github_days_since_last_push = {
      title       = "Days Since Last Push"
      description = "Number of days since the last code push"
      icon        = "Clock"
      type        = "number"
      calculation = "if .properties.github_last_push != null then ((now - (.properties.github_last_push[0:19] + \"Z\" | fromdateiso8601)) / 86400 | floor) else 9999 end"
    }
    github_failure_rate_trend = {
      title       = "Workflow Failure Rate Trend"
      description = "Weekly failure rate vs monthly average"
      icon        = "DefaultProperty"
      type        = "string"
      calculation = "((if (.properties.github_workflow_runs_30d != null and .properties.github_workflow_runs_30d != 0) then ((.properties.github_failed_workflow_runs_30d // 0) / .properties.github_workflow_runs_30d) * 100 | floor else 0 end) - (if (.properties.github_workflow_runs_7d != null and .properties.github_workflow_runs_7d != 0) then ((.properties.github_failed_workflow_runs_7d // 0) / .properties.github_workflow_runs_7d) * 100 | floor else 0 end)) as $diff | if $diff > 0 then \"Improving\" elif $diff < 0 then \"Degrading\" else \"Stable\" end"
      colorized   = true
      colors = {
        Improving = "green"
        Stable    = "blue"
        Degrading = "red"
      }
    }
    github_lead_time_tier = {
      title       = "Lead Time for Changes (GitHub)"
      description = "DORA lead time for changes tier (from GitHub PR cycle time)"
      icon        = "DefaultProperty"
      type        = "string"
      calculation = "if (.properties.github_lead_time_for_change == null) then \"Low\" elif .properties.github_lead_time_for_change <= 24 then \"Elite\" elif .properties.github_lead_time_for_change <= 168 then \"High\" elif .properties.github_lead_time_for_change <= 720 then \"Medium\" else \"Low\" end"
      colorized   = true
      colors = {
        Elite  = "lime"
        High   = "blue"
        Medium = "orange"
        Low    = "red"
      }
    }
    github_monthly_workflow_failure_rate = {
      title       = "Monthly Workflow Failure Rate (%)"
      description = "Percentage of workflow runs that failed in the last 30 days"
      icon        = "DefaultProperty"
      type        = "number"
      calculation = "if (.properties.github_workflow_runs_30d != null and .properties.github_workflow_runs_30d != 0) then ((.properties.github_failed_workflow_runs_30d // 0) / .properties.github_workflow_runs_30d) * 100 | floor else 0 end"
    }
    github_stale_pr_share_percent = {
      title       = "Stale PR Share (%)"
      description = "Percentage of open PRs that are older than 7 days"
      icon        = "DefaultProperty"
      type        = "number"
      calculation = "if (.properties.github_open_prs != null and .properties.github_open_prs != 0) then (.properties.github_stale_prs_7d / .properties.github_open_prs) * 100 else 0 end"
    }
    github_throughput_trend = {
      title       = "PR Throughput Trend"
      description = "Weekly vs monthly PR throughput rate"
      icon        = "DefaultProperty"
      type        = "string"
      calculation = "((.properties.github_merged_prs_last_week // 0) * 30 - (.properties.github_merged_prs_last_month // 0) * 7) as $diff | if $diff > 0 then \"Improving\" elif $diff < 0 then \"Degrading\" else \"Stable\" end"
      colorized   = true
      colors = {
        Improving = "green"
        Stable    = "blue"
        Degrading = "red"
      }
    }
    github_weekly_workflow_failure_rate = {
      title       = "Weekly Workflow Failure Rate (%)"
      description = "Percentage of workflow runs that failed in the last 7 days"
      icon        = "DefaultProperty"
      type        = "number"
      calculation = "if (.properties.github_workflow_runs_7d != null and .properties.github_workflow_runs_7d != 0) then ((.properties.github_failed_workflow_runs_7d // 0) / .properties.github_workflow_runs_7d) * 100 | floor else 0 end"
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

  # Added by the GitHub Ocean integration; adopted into code on Day 14.
  mirror_properties = {
    github_lead_time_hours = { path = "github_pull_request.cycle_time_hours", title = "Lead Time for Changes (Hours)" }
    github_repo_id         = { path = "github_pull_request.repository.$identifier", title = "GitHub Repository ID" }
  }

  relations = {
    service = {
      title    = "Service"
      target   = port_blueprint.service.identifier
      required = false # Port has it as not required; kept to match reality
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
