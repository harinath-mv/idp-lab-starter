# Day 12 – GitHub Ocean + JQ notes

## 5 JQ lines (run in Git Bash, folder ~/jq-lab)

1. Identifier of a repo
   jq '.name' repo.json
   Output: "idp-lab-starter"   → mapping: identifier: .name

2. Default value when empty
   jq '.description // "No description yet"' repo.json
   Output: "No description yet"   → // means "if empty, use this"

3. Selector test (true = take it, false = skip it)
   jq '.name | startswith("idp")' repo.json
   Output: true   → mapping: selector.query

4. PR identifier (same as Port)
   jq '.[] | .head.repo.name + "-pr-" + (.number | tostring)' prs.json
   Output: "idp-lab-starter-pr-1"   → tostring turns the number 1 into text "1"

5. PR status (merged / closed / open)
   jq '.[] | if .merged_at != null then "merged" elif .state == "closed" then "closed" else "open" end' prs.json
   Output: "merged"   → GitHub only says "closed"; the mapping works out "merged"

## Lesson learned
Mapping would not save: "Property createdAt does not exist on blueprint deployment".
Cause: Day 11 Terraform removed sample properties from the Deployment blueprint,
but the GitHub mapping still used them (PR → deployment block).
Fix today: removed that block. Proper fix later: add the properties in blueprints.tf (Day 14/15).