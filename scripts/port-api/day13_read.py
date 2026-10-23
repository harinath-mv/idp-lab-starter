"""Day 13 Part C: READ. Look at the service blueprint, then list entities."""
from port_api import call, log

# 1. What does the 'service' form (blueprint) look like?
status, data = call("GET", "/blueprints/service")
if status == 200:
    schema = data.get("blueprint", {}).get("schema", {})
    required = schema.get("required", [])
    log("Properties on the 'service' blueprint:")
    for name, spec in schema.get("properties", {}).items():
        flag = "  <-- REQUIRED" if name in required else ""
        print(f"     - {name}  (type: {spec.get('type')}){flag}")

# 2. The repos that GitHub Ocean created on Day 12
status, data = call("GET", "/blueprints/githubRepository/entities")
if status == 200:
    entities = data.get("entities", [])
    log(f"githubRepository entities: {len(entities)}")
    for e in entities:
        p = e.get("properties", {})
        print(f"     - {e['identifier']} | language={p.get('language')} | branch={p.get('defaultBranch')}")

# 3. The services that exist today (Day 11 + anything you create)
status, data = call("GET", "/blueprints/service/entities")
if status == 200:
    entities = data.get("entities", [])
    log(f"service entities: {len(entities)}")
    for e in entities:
        print(f"     - {e['identifier']} | title={e.get('title')}")
