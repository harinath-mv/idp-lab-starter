"""GitHub webhook receiver.

Day 18: signature check (401 for anything not signed by GitHub).
Day 19: duplicate-delivery guard (X-GitHub-Delivery) after the signature check.
Day 20: JSON logs with the delivery ID on every line + one summary line per request.

Endpoints
  GET  /healthz           -> is the service up?
  POST /webhooks/github   -> receives GitHub events
"""

import logging
import time

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import ValidationError

from app.config import get_settings
from app.dedupe import DeliveryDeduper
from app.logging_setup import delivery_id_var, event_var, setup_logging
from app.models import PullRequestEvent
from app.security import is_valid_signature

_settings = get_settings()
setup_logging(_settings.log_level, _settings.log_format)
log = logging.getLogger("github-webhook")

app = FastAPI(title="github-webhook", version="0.3.0")
deduper = DeliveryDeduper(ttl_seconds=_settings.dedupe_ttl_seconds, max_entries=_settings.dedupe_max_entries)


@app.middleware("http")
async def request_context_and_summary(request: Request, call_next):
    """Tag every log line of this request with its delivery ID, then log one summary line."""
    delivery_token = delivery_id_var.set(request.headers.get("x-github-delivery", ""))
    event_token = event_var.set(request.headers.get("x-github-event", ""))
    started = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        if request.url.path != "/healthz":  # health checks every 30 s would drown the logs
            log.info(
                "request finished",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status": status,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                },
            )
        delivery_id_var.reset(delivery_token)
        event_var.reset(event_token)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "remembered_deliveries": len(deduper)}


def process_event(event_type: str, delivery_id: str, body: bytes) -> dict:
    """Do the real work for one verified, first-time delivery."""
    if event_type == "ping":
        log.info("Ping received (delivery %s)", delivery_id)
        return {"ok": True, "event": "ping", "message": "pong"}

    if event_type == "pull_request":
        try:
            event = PullRequestEvent.model_validate_json(body)
        except ValidationError as err:
            log.warning("Delivery %s: payload did not match the model: %s", delivery_id, err.errors()[:2])
            raise HTTPException(status_code=422, detail="unexpected pull_request payload") from err

        pr = event.pull_request
        log.info(
            "PR #%s %s in %s by %s: %s",
            pr.number,
            event.action,
            event.repository.full_name,
            pr.user.login,
            pr.title,
        )
        # Weekend: PortClient(...).upsert_entity(...) goes here (Day 19 built the retrying client).
        return {
            "ok": True,
            "event": "pull_request",
            "action": event.action,
            "repo": event.repository.full_name,
            "number": pr.number,
            "title": pr.title,
        }

    log.info("Ignored event '%s' (delivery %s)", event_type, delivery_id)
    return {"ok": True, "event": event_type, "ignored": True}


@app.post("/webhooks/github", status_code=200)
async def github_webhook(
    request: Request,
    x_github_event: str = Header(default=""),
    x_github_delivery: str = Header(default=""),
    x_hub_signature_256: str | None = Header(default=None),
) -> dict:
    settings = get_settings()

    # 1. Fail closed: no secret configured = we cannot check anything = accept nothing.
    if not settings.github_webhook_secret:
        log.error("GITHUB_WEBHOOK_SECRET is not set; rejecting delivery %s", x_github_delivery)
        raise HTTPException(status_code=503, detail="webhook secret not configured")

    # 2. Check the signature on the RAW bytes, before parsing anything.
    body = await request.body()
    if not is_valid_signature(settings.github_webhook_secret, body, x_hub_signature_256):
        log.warning("Rejected delivery %s: bad or missing signature", x_github_delivery)
        raise HTTPException(status_code=401, detail="invalid signature")

    # 3. Day 19: skip deliveries we already processed. AFTER the signature check,
    #    so nobody can fill our memory with fake IDs.
    if deduper.already_processed(x_github_delivery):
        log.info("Duplicate delivery %s skipped", x_github_delivery)
        return {"ok": True, "duplicate": True, "delivery": x_github_delivery}

    # 4. Do the work. Remember the ID only if it succeeded, so a failed event can be redelivered.
    result = process_event(x_github_event, x_github_delivery, body)
    deduper.mark_processed(x_github_delivery)
    return result
