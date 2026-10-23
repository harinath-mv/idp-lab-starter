"""Day 13 cleanup: DELETE every service whose identifier starts with 'day13-'."""
from port_api import call, log

status, data = call("GET", "/blueprints/service/entities")
targets = [e["identifier"] for e in data.get("entities", []) if e["identifier"].startswith("day13-")]
log(f"Will delete {len(targets)} entities: {targets}")
for ident in targets:
    call("DELETE", f"/blueprints/service/entities/{ident}")
    status, _ = call("GET", f"/blueprints/service/entities/{ident}")
    log(f"{ident}: after delete, GET returns {status} (404 = gone)")
