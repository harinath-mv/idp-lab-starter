"""Day 20: logs are JSON and carry the delivery ID."""

import json
import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.logging_setup import JsonFormatter, delivery_id_var
from app.main import app
from app.security import expected_signature

SECRET = "test-secret-123"
PAYLOAD = (Path(__file__).parent / "payloads" / "pull_request_opened.json").read_bytes()


def test_formatter_outputs_one_json_object_with_fields():
    token = delivery_id_var.set("abc-1")
    try:
        record = logging.getLogger("t").makeRecord("t", logging.INFO, "f.py", 1, "hello %s", ("world",), None)
    finally:
        delivery_id_var.reset(token)
    record.status = 200  # what extra={"status": 200} does
    line = JsonFormatter().format(record)
    data = json.loads(line)  # proves it is valid JSON
    assert data["msg"] == "hello world"
    assert data["level"] == "INFO"
    assert data["delivery_id"] == "abc-1"
    assert data["status"] == 200
    assert data["ts"].endswith("Z")


def test_request_logs_carry_the_delivery_id(monkeypatch, caplog):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", SECRET)
    headers = {
        "X-GitHub-Event": "pull_request",
        "X-GitHub-Delivery": "trace-me-123",
        "X-Hub-Signature-256": expected_signature(SECRET, PAYLOAD),
        "Content-Type": "application/json",
    }
    with caplog.at_level(logging.INFO, logger="github-webhook"):
        TestClient(app).post("/webhooks/github", content=PAYLOAD, headers=headers)
    lines = [json.loads(JsonFormatter().format(r)) for r in caplog.records]
    summary = [entry for entry in lines if entry["msg"] == "request finished"]
    assert summary, "expected one summary line per request"
    assert summary[0]["status"] == 200
    assert summary[0]["path"] == "/webhooks/github"
    assert "duration_ms" in summary[0]
    assert summary[0]["delivery_id"] == "trace-me-123"
    pr_lines = [entry for entry in lines if entry["msg"].startswith("PR #42")]
    assert pr_lines[0]["delivery_id"] == "trace-me-123"  # the business log line is tagged too
    assert pr_lines[0]["event"] == "pull_request"


@pytest.mark.parametrize("bad", ["xml", "JSON", ""])
def test_log_format_setting_is_validated(monkeypatch, bad):
    from pydantic import ValidationError

    from app.config import get_settings

    monkeypatch.setenv("LOG_FORMAT", bad)
    with pytest.raises(ValidationError):
        get_settings()
