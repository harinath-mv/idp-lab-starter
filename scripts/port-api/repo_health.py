"""Day 16: backend of the 'Repo health check' self-service action.

Reads the run payload (env vars set by the workflow), does real work against the GitHub API,
and reports progress + a summary back to the Port run.
"""
import datetime as dt
import os
import sys

import requests

from port_run import port_log, port_patch

REPO = os.environ["REPO"]                       # e.g. harinath-mv/idp-lab-starter
DAYS = int(float(os.environ.get("DAYS", "7")))  # Port sends numbers as text, so convert
GH = {"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
      "Accept": "application/vnd.github+json"}


def parse(ts):
    return dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))


def main():
    now = dt.datetime.now(dt.timezone.utc)
    port_log(f"Started health check for {REPO} (last {DAYS} days)")

    r = requests.get(f"https://api.github.com/repos/{REPO}/pulls",
                     headers=GH, params={"state": "all", "per_page": 100}, timeout=30)
    r.raise_for_status()
    prs = r.json()

    open_prs = [p for p in prs if p["state"] == "open"]
    merged = [p for p in prs if p.get("merged_at") and parse(p["merged_at"]) >= now - dt.timedelta(days=DAYS)]
    stale = [p for p in open_prs if parse(p["created_at"]) < now - dt.timedelta(days=7)]

    port_log(f"Open PRs: {len(open_prs)}")
    port_log(f"PRs merged in the last {DAYS} days: {len(merged)}")
    port_log(f"Open PRs older than 7 days (stale): {len(stale)}")

    summary = f"{len(open_prs)} open, {len(merged)} merged in {DAYS}d, {len(stale)} stale"
    port_patch(summary=summary, link=[os.environ.get("RUN_URL", "")])
    port_log(f"Done: {summary}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # report the failure to the developer in Port, then fail the job
        port_log(f"Health check FAILED: {exc}")
        sys.exit(1)