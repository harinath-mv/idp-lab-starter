"""Send a signed (or deliberately badly signed) test event to the local receiver.

Usage (service must be running):
  python tools/send_test_event.py            -> correct signature  (expect 200)
  python tools/send_test_event.py --bad      -> wrong signature    (expect 401)
  python tools/send_test_event.py --nosig    -> no signature       (expect 401)
Uses only the Python standard library, so it works without extra installs.
"""

import hashlib
import hmac
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

URL = os.getenv("WEBHOOK_URL", "http://127.0.0.1:8000/webhooks/github")
SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")
BODY = (Path(__file__).resolve().parent.parent / "tests" / "payloads" / "pull_request_opened.json").read_bytes()

if not SECRET:
    sys.exit("Set GITHUB_WEBHOOK_SECRET first (same value the service uses).")

headers = {"Content-Type": "application/json", "X-GitHub-Event": "pull_request", "X-GitHub-Delivery": "local-test-1"}
if "--nosig" not in sys.argv:
    key = b"wrong-secret" if "--bad" in sys.argv else SECRET.encode()
    headers["X-Hub-Signature-256"] = "sha256=" + hmac.new(key, BODY, hashlib.sha256).hexdigest()

req = urllib.request.Request(URL, data=BODY, headers=headers, method="POST")
try:
    with urllib.request.urlopen(req) as resp:
        print(resp.status, resp.read().decode())
except urllib.error.HTTPError as err:
    print(err.code, err.read().decode())
