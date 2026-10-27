"""Platform helper for self-service workflows: talk to the Port run that started this workflow.

Usage (inside a GitHub Actions step, with PORT_CLIENT_ID, PORT_CLIENT_SECRET and RUN_ID set):
  python port_run.py log "some message"           -> adds a line to the run's log in Port
  python port_run.py link "https://..."           -> adds a link (e.g. the GitHub run) to the run
  python port_run.py summary "short result text"  -> sets the run's summary
"""
import os
import sys

from port_api import call, log

RUN_ID = os.environ.get("RUN_ID", "")


def port_log(message):
    log(message)
    if RUN_ID:
        call("POST", f"/actions/runs/{RUN_ID}/logs", body={"message": message})


def port_patch(**fields):
    if RUN_ID:
        call("PATCH", f"/actions/runs/{RUN_ID}", body=fields)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("usage: python port_run.py log|link|summary <text>")
    cmd, text = sys.argv[1], " ".join(sys.argv[2:])
    if cmd == "log":
        port_log(text)
    elif cmd == "link":
        port_patch(link=[text])
    elif cmd == "summary":
        port_patch(summary=text)
    else:
        sys.exit(f"unknown command: {cmd}")