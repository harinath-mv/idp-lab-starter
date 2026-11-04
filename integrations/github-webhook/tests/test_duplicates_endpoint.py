"""Day 19: the webhook endpoint processes each delivery ID only once."""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import main
from app.main import app
from app.security import expected_signature

SECRET = "test-secret-123"
PAYLOAD = (Path(__file__).parent / "payloads" / "pull_request_opened.json").read_bytes()


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", SECRET)
    return TestClient(app)


def deliver(client, delivery_id: str, signature: str | None = None):
    headers = {
        "X-GitHub-Event": "pull_request",
        "X-GitHub-Delivery": delivery_id,
        "X-Hub-Signature-256": signature or expected_signature(SECRET, PAYLOAD),
        "Content-Type": "application/json",
    }
    return client.post("/webhooks/github", content=PAYLOAD, headers=headers)


def test_same_delivery_twice_is_processed_once(client):
    with patch.object(main, "process_event", wraps=main.process_event) as spy:
        first = deliver(client, "delivery-111")
        second = deliver(client, "delivery-111")
    assert first.status_code == 200 and "duplicate" not in first.json()
    assert second.status_code == 200 and second.json()["duplicate"] is True
    assert spy.call_count == 1  # the real work happened once


def test_different_deliveries_are_both_processed(client):
    with patch.object(main, "process_event", wraps=main.process_event) as spy:
        deliver(client, "delivery-1")
        deliver(client, "delivery-2")
    assert spy.call_count == 2


def test_failed_delivery_is_not_remembered_so_a_redelivery_is_processed(client):
    boom = HTTPException(status_code=502, detail="Port unavailable")
    with patch.object(main, "process_event", side_effect=[boom, {"ok": True}]) as fake:
        first = deliver(client, "delivery-222")
        second = deliver(client, "delivery-222")  # GitHub "Redeliver"
    assert first.status_code == 502
    assert second.status_code == 200 and second.json() == {"ok": True}
    assert fake.call_count == 2


def test_badly_signed_duplicate_does_not_touch_the_memory(client):
    resp = deliver(client, "delivery-333", signature="sha256=" + "0" * 64)
    assert resp.status_code == 401
    assert main.deduper.already_processed("delivery-333") is False
