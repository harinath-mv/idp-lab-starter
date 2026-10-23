"""Day 13 Part D: CREATE (upsert + merge) one service entity."""
from port_api import call, log

entity = {
    "identifier": "day13-payments-api",   # unique key, never change it later
    "title": "Payments API (Day 13)",
    "properties": {},                     # add REQUIRED properties here if Part C showed any
}

status, data = call("POST", "/blueprints/service/entities",
                    body=entity, params={"upsert": "true", "merge": "true"})
if status in (200, 201):
    e = data.get("entity", {})
    log(f"OK: {e.get('identifier')} now exists with title '{e.get('title')}'")
