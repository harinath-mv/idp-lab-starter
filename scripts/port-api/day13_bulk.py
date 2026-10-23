"""Day 13 Part F: load several services from a list (a mini migration). Safe to run twice."""
from port_api import call, log

services = [
    {"identifier": "day13-orders-api",   "title": "Orders API (Day 13)"},
    {"identifier": "day13-billing-api",  "title": "Billing API (Day 13)"},
    {"identifier": "day13-notify-worker", "title": "Notify Worker (Day 13)"},
]

ok = failed = 0
for s in services:
    status, _ = call("POST", "/blueprints/service/entities",
                     body=s, params={"upsert": "true", "merge": "true"})
    if status in (200, 201):
        ok += 1
    else:
        failed += 1
log(f"Done: {ok} OK, {failed} failed")
