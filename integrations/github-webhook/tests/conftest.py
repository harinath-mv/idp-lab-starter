"""Shared test setup: every test starts with an empty duplicate memory."""

import pytest

from app import main
from app.dedupe import DeliveryDeduper


@pytest.fixture(autouse=True)
def fresh_deduper(monkeypatch):
    monkeypatch.setattr(main, "deduper", DeliveryDeduper())
