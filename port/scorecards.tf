# Day 14: grade every GitHub repo. Properties come from the Day 12 GitHub Ocean mapping.
resource "port_scorecard" "repo_readiness" {
  identifier = "repoReadiness"
  title      = "Repository readiness"
  blueprint  = "githubRepository"

  rules = [
    {
      identifier = "hasReadme"
      title      = "Has a README"
      level      = "Bronze"
      query = {
        combinator = "and"
        conditions = [jsonencode({ property = "readme", operator = "isNotEmpty" })]
      }
    },
    {
      identifier = "hasDescription"
      title      = "Has a description"
      level      = "Silver"
      query = {
        combinator = "and"
        conditions = [jsonencode({ property = "description", operator = "isNotEmpty" })]
      }
    },
    {
      identifier = "hasCodeowners"
      title      = "Has a CODEOWNERS file"
      level      = "Gold"
      query = {
        combinator = "and"
        conditions = [jsonencode({ property = "codeowners", operator = "isNotEmpty" })]
      }
    }
  ]
}