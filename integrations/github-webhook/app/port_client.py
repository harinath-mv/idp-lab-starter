"""Day 19: a small Port API client that is polite under pressure.

- Gets an access token once and reuses it until shortly before it expires.
- Retries temporary failures: 429 (honours Retry-After), 5xx, network errors.
- Refreshes the token once on 401.
- Fails fast on mistakes that a retry cannot fix (400, 403, 404, 422).
"""

import logging
import random
import time
from collections.abc import Callable
from email.utils import parsedate_to_datetime

import httpx
from tenacity import RetryCallState, Retrying, retry_if_exception_type, stop_after_attempt

log = logging.getLogger("github-webhook.port")

RETRYABLE_STATUS = {429, 500, 502, 503, 504}
MAX_ATTEMPTS = 5
BASE_DELAY = 0.5  # seconds: 0.5, 1, 2, 4 ...
MAX_DELAY = 30.0  # never wait longer than this, even if Retry-After asks for more


class PortApiError(Exception):
    """A Port call failed and retrying will not help (or we ran out of attempts)."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class RetryableError(Exception):
    """A temporary failure: worth another try."""

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


def parse_retry_after(value: str | None) -> float | None:
    """Retry-After is either seconds ("2") or an HTTP date. Returns seconds, or None."""
    if not value:
        return None
    value = value.strip()
    if value.isdigit():
        return float(value)
    try:
        when = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, when.timestamp() - time.time())


def wait_time(retry_state: RetryCallState) -> float:
    """How long to wait before the next attempt."""
    error = retry_state.outcome.exception() if retry_state.outcome else None
    if isinstance(error, RetryableError) and error.retry_after is not None:
        return min(error.retry_after, MAX_DELAY)  # the server told us: obey (within reason)
    backoff = BASE_DELAY * 2 ** (retry_state.attempt_number - 1)  # 0.5, 1, 2, 4
    return min(backoff, MAX_DELAY) + random.uniform(0, 0.25)  # + jitter


def log_before_sleep(retry_state: RetryCallState) -> None:
    error = retry_state.outcome.exception() if retry_state.outcome else None
    wait = retry_state.next_action.sleep if retry_state.next_action else 0
    log.warning(
        "Port call failed (%s); retrying in %.1fs (attempt %d/%d)",
        error,
        wait,
        retry_state.attempt_number,
        MAX_ATTEMPTS,
    )


class PortClient:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str = "https://api.port.io/v1",
        http: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        if not client_id or not client_secret:
            raise ValueError("PORT_CLIENT_ID and PORT_CLIENT_SECRET are required")
        self._client_id = client_id
        self._client_secret = client_secret
        self._http = http or httpx.Client(base_url=base_url, timeout=10.0)
        self._sleep = sleep  # injectable so tests do not really wait
        self._token: str | None = None
        self._token_expires_at = 0.0

    # ---- token -------------------------------------------------------------
    def _get_token(self, force: bool = False) -> str:
        if self._token and not force and time.time() < self._token_expires_at - 60:
            return self._token
        resp = self._send(
            "POST",
            "/auth/access_token",
            json={"clientId": self._client_id, "clientSecret": self._client_secret},
            auth=False,
        )
        data = resp.json()
        self._token = data["accessToken"]
        self._token_expires_at = time.time() + float(data.get("expiresIn", 3600))
        return self._token

    # ---- one HTTP attempt ----------------------------------------------------
    def _attempt(self, method: str, path: str, auth: bool, **kwargs) -> httpx.Response:
        headers = kwargs.pop("headers", {})
        if auth:
            headers["Authorization"] = f"Bearer {self._get_token()}"
        try:
            resp = self._http.request(method, path, headers=headers, **kwargs)
        except httpx.TransportError as err:  # DNS, refused connection, timeout ...
            raise RetryableError(f"network error: {err.__class__.__name__}") from err

        if auth and resp.status_code == 401:
            self._get_token(force=True)  # token expired: refresh, then let the retry use it
            raise RetryableError("401 unauthorized (token refreshed)")
        if resp.status_code in RETRYABLE_STATUS:
            raise RetryableError(
                f"HTTP {resp.status_code}", retry_after=parse_retry_after(resp.headers.get("Retry-After"))
            )
        if resp.status_code >= 400:
            raise PortApiError(f"{method} {path} -> HTTP {resp.status_code}: {resp.text[:200]}", resp.status_code)
        return resp

    # ---- attempts with retry -----------------------------------------------
    def _send(self, method: str, path: str, auth: bool = True, **kwargs) -> httpx.Response:
        retrying = Retrying(
            retry=retry_if_exception_type(RetryableError),
            stop=stop_after_attempt(MAX_ATTEMPTS),
            wait=wait_time,
            sleep=self._sleep,
            before_sleep=log_before_sleep,
            reraise=True,
        )
        try:
            return retrying(self._attempt, method, path, auth, **kwargs)
        except RetryableError as err:
            raise PortApiError(f"{method} {path} gave up after {MAX_ATTEMPTS} attempts: {err}") from err

    # ---- public API ----------------------------------------------------------
    def get_blueprint(self, identifier: str) -> dict:
        return self._send("GET", f"/blueprints/{identifier}").json()

    def upsert_entity(self, blueprint: str, entity: dict) -> dict:
        """Create or update an entity. Safe to repeat: same identifier = same entity (idempotent)."""
        resp = self._send(
            "POST", f"/blueprints/{blueprint}/entities", params={"upsert": "true", "merge": "true"}, json=entity
        )
        return resp.json()
