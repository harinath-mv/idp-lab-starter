"""Day 20: list every entity of a blueprint through the paginated search (read-only).

Usage (with the Day 13 credentials exported):
  python tools/port_list.py                 -> all services
  python tools/port_list.py githubRepository 5   -> page size 5, to watch several pages
"""

import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # so "app" can be imported

from app.port_client import PortApiError, PortClient  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

blueprint = sys.argv[1] if len(sys.argv) > 1 else "service"
page_size = int(sys.argv[2]) if len(sys.argv) > 2 else 100
client = PortClient(
    os.getenv("PORT_CLIENT_ID", ""),
    os.getenv("PORT_CLIENT_SECRET", ""),
    base_url=os.getenv("PORT_API_URL", "https://api.port.io/v1"),
)
try:
    count = 0
    for entity in client.search_entities(blueprint, page_size=page_size):
        count += 1
        print(f"{count:4}  {entity.get('identifier')}  ({entity.get('title')})")
except PortApiError as err:
    sys.exit(f"FAILED: {err}")
print(f"Total: {count} {blueprint} entities")
