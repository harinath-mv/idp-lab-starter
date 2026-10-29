"""Day 18 tests. Run:  python -m pytest -v"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.security import expected_signature

SECRET = "test-secret-123"
PAYLOAD = (Path(__file__).parent / "payloads" / "pull_request_opened.json").read_bytes()


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", SECRET)
    return TestClient(app)


def send(client, body: bytes, event: str = "pull_request", signature: str | None = "auto"):
    headers = {"X-GitHub-Event": event, "X-GitHub-Delivery": "test-delivery-1", "Content-Type": "application/json"}
    if signature == "auto":
        signature = expected_signature(SECRET, body)
    if signature is not None:
        headers["X-Hub-Signature-256"] = signature
    return client.post("/webhooks/github", content=body, headers=headers)


def test_health(client):
    assert client.get("/healthz").json() == {"status": "ok"}


def test_valid_signature_is_accepted_and_parsed(client):
    resp = send(client, PAYLOAD)
    assert resp.status_code == 200
    data = resp.json()
    assert data["number"] == 42
    assert data["repo"] == "harinath-mv/idp-lab-starter"


def test_wrong_signature_is_rejected(client):
    resp = send(client, PAYLOAD, signature="sha256=" + "0" * 64)
    assert resp.status_code == 401


def test_missing_signature_is_rejected(client):
    resp = send(client, PAYLOAD, signature=None)
    assert resp.status_code == 401


def test_signature_made_with_another_secret_is_rejected(client):
    resp = send(client, PAYLOAD, signature=expected_signature("someone-elses-secret", PAYLOAD))
    assert resp.status_code == 401


def test_tampered_body_is_rejected(client):
    good_sig = expected_signature(SECRET, PAYLOAD)
    tampered = PAYLOAD.replace(b'"opened"', b'"closed"')
    resp = send(client, tampered, signature=good_sig)
    assert resp.status_code == 401


def test_reformatted_json_is_rejected(client):
    """Same data, different bytes (spaces removed) = different signature.
    This is why we must check the RAW body, never a re-serialised copy."""
    good_sig = expected_signature(SECRET, PAYLOAD)
    compact = json.dumps(json.loads(PAYLOAD), separators=(",", ":")).encode()
    resp = send(client, compact, signature=good_sig)
    assert resp.status_code == 401


def test_no_secret_configured_fails_closed(monkeypatch):
    monkeypatch.delenv("GITHUB_WEBHOOK_SECRET", raising=False)
    resp = send(TestClient(app), PAYLOAD)
    assert resp.status_code == 503


def test_ping_event(client):
    body = b'{"zen": "Keep it logically awesome."}'
    resp = send(client, body, event="ping")
    assert resp.status_code == 200
    assert resp.json()["message"] == "pong"


def test_unhandled_event_is_accepted_but_ignored(client):
    body = b'{"ref": "refs/heads/main"}'
    resp = send(client, body, event="push")
    assert resp.status_code == 200
    assert resp.json()["ignored"] is True


def test_signed_but_malformed_pull_request_returns_422(client):
    body = b'{"action": "opened"}'
    resp = send(client, body)
    assert resp.status_code == 422
