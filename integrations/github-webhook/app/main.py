"""Day 18: GitHub webhook receiver.

Endpoints
  GET  /healthz           -> is the service up?
  POST /webhooks/github   -> receives GitHub events, rejects anything not signed by GitHub
"""

import logging

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import ValidationError

from app.config import get_settings
from app.models import PullRequestEvent
from app.security import is_valid_signature

logging.basicConfig(level=get_settings().log_level, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github-webhook")

app = FastAPI(title="github-webhook", version="0.1.0")


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


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

    # 3. Only now do we trust the content.
    if x_github_event == "ping":
        log.info("Ping received (delivery %s)", x_github_delivery)
        return {"ok": True, "event": "ping", "message": "pong"}

    if x_github_event == "pull_request":
        try:
            event = PullRequestEvent.model_validate_json(body)
        except ValidationError as err:
            log.warning("Delivery %s: payload did not match the model: %s", x_github_delivery, err.errors()[:2])
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
        # Day 20/weekend: this is where we will upsert the PR into the Port catalog.
        return {
            "ok": True,
            "event": "pull_request",
            "action": event.action,
            "repo": event.repository.full_name,
            "number": pr.number,
            "title": pr.title,
        }

    # Signed, but an event type we do not handle yet: accept it so GitHub does not mark it failed.
    log.info("Ignored event '%s' (delivery %s)", x_github_event, x_github_delivery)
    return {"ok": True, "event": x_github_event, "ignored": True}
