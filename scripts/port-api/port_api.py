"""Day 13 helper: everything needed to talk to the Port API.

Other scripts import call() and log() from here, so the login code lives in ONE place.
"""
import os
import sys

import requests

# EU = https://api.port.io/v1 (default)   US = https://api.us.port.io/v1
API_URL = os.environ.get("PORT_API_URL", "https://api.port.io/v1")
_token = None  # filled the first time call() needs it


def log(msg):
    print(f"[day13] {msg}")


def mask(value):
    """Show only the first 6 characters of a secret or token (Day 11 habit)."""
    if not value:
        return "<empty>"
    return value[:6] + "..." + f"({len(value)} chars)"


def get_token():
    """Day 2 client credentials: send ID + secret, get an access token back."""
    client_id = os.environ.get("PORT_CLIENT_ID")
    client_secret = os.environ.get("PORT_CLIENT_SECRET")
    if not client_id or not client_secret:
        sys.exit("[day13] PORT_CLIENT_ID / PORT_CLIENT_SECRET are not set. Run the two 'read' commands (Part B) first.")

    log(f"Logging in to {API_URL} with client ID {mask(client_id)}")
    r = requests.post(f"{API_URL}/auth/access_token",
                      json={"clientId": client_id, "clientSecret": client_secret},
                      timeout=30)
    if r.status_code != 200:
        log(f"Login FAILED: HTTP {r.status_code} -> {r.text[:200]}")
        sys.exit(1)
    token = r.json()["accessToken"]
    log(f"Got access token {mask(token)}")
    return token


def call(method, path, body=None, params=None):
    """One API call. Returns (status_code, json_data). Never prints the token."""
    global _token
    if _token is None:
        _token = get_token()
    r = requests.request(method, f"{API_URL}{path}",
                         headers={"Authorization": f"Bearer {_token}"},
                         json=body, params=params, timeout=30)
    log(f"{method} {path} -> HTTP {r.status_code}")
    try:
        data = r.json()
    except ValueError:
        data = {"raw": r.text[:200]}
    if r.status_code >= 400:
        log(f"ERROR message from Port: {data.get('message', data)}")
    return r.status_code, data
