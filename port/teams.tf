# Day 19 (Part 2): teams, defined as code.
#
# A team groups people. A service "owned" by a team can then be managed by that team only.
# Users must already exist in Port (invited on Day 18) before they can be added here.

locals {
  # CHANGE THIS to the second email you invited as a Member on Day 18.
  lab_developer_email = "REPLACE-with-your-day18-developer-email"
}

resource "port_team" "payments" {
  name        = "payments"
  description = "Payments developers (Day 19 lab)"
  users       = ["harinathmv1@gmail.com"]
}
