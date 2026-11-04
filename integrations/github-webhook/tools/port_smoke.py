"""Day 19: one real call to Port through the retrying client (read-only).

Usage (with the Day 13 credentials exported):
  export PORT_CLIENT_ID=...  PORT_CLIENT_SECRET=...
  python tools/port_smoke.py            -> reads the 'service' blueprint
  python tools/port_smoke.py s3Bucket   -> reads another blueprint
"""

import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # so "app" can be imported

from app.port_client import PortApiError, PortClient  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

blueprint = sys.argv[1] if len(sys.argv) > 1 else "service"
client = PortClient(
    os.getenv("PORT_CLIENT_ID", ""),
    os.getenv("PORT_CLIENT_SECRET", ""),
    base_url=os.getenv("PORT_API_URL", "https://api.port.io/v1"),
)
try:
    data = client.get_blueprint(blueprint)
except PortApiError as err:
    sys.exit(f"FAILED: {err}")
bp = data.get("blueprint", data)
print(f"OK: blueprint '{bp.get('identifier')}' titled '{bp.get('title')}'")
