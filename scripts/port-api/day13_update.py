"""Day 13 Part E: UPDATE only some fields (PATCH), then read back."""
from port_api import call, log

ENTITY = "/blueprints/service/entities/day13-payments-api"
PROP_NAME = ""          # <-- put a STRING property name from Part C here, e.g. "language"
PROP_VALUE = "Python"   # <-- a value that makes sense for that property

body = {"title": "Payments API (Day 13, updated by script)"}
if PROP_NAME:
    body["properties"] = {PROP_NAME: PROP_VALUE}

status, data = call("PATCH", ENTITY, body=body)

# Read it back to prove the change really happened (Day 7-9 habit: change, then verify)
status, data = call("GET", ENTITY)
if status == 200:
    e = data.get("entity", {})
    log(f"title      = {e.get('title')}")
    log(f"properties = {e.get('properties')}")
