"""Day 19: PortClient retries, Retry-After, token handling, fail-fast.

No real network: httpx.MockTransport plays "Port" and returns the responses we script.
No real waiting: we pass a Mock as the sleep function and check what it was asked to wait.
"""

from unittest.mock import Mock

import httpx
import pytest

from app.port_client import MAX_ATTEMPTS, PortApiError, PortClient, parse_retry_after

TOKEN_OK = httpx.Response(200, json={"accessToken": "tok-1", "expiresIn": 3600})


def make_client(responses: list):
    """A PortClient whose HTTP calls return `responses` in order (after the token call)."""
    calls = []
    queue = list(responses)

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path.endswith("/auth/access_token"):
            return TOKEN_OK
        item = queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    http = httpx.Client(base_url="https://api.port.io/v1", transport=httpx.MockTransport(handler))
    sleep = Mock()
    client = PortClient("id", "secret", http=http, sleep=sleep)
    api_calls = lambda: [c for c in calls if not c.url.path.endswith("/auth/access_token")]  # noqa: E731
    return client, sleep, api_calls, calls


def test_success_first_time_no_sleep():
    client, sleep, api_calls, _ = make_client([httpx.Response(200, json={"identifier": "service"})])
    assert client.get_blueprint("service")["identifier"] == "service"
    assert len(api_calls()) == 1
    sleep.assert_not_called()


def test_429_waits_for_retry_after_then_succeeds():
    client, sleep, api_calls, _ = make_client(
        [
            httpx.Response(429, headers={"Retry-After": "2"}),
            httpx.Response(429, headers={"Retry-After": "3"}),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    assert client.upsert_entity("service", {"identifier": "orders-api"}) == {"ok": True}
    assert len(api_calls()) == 3
    assert [c.args[0] for c in sleep.call_args_list] == [2.0, 3.0]  # obeyed the server exactly


def test_huge_retry_after_is_capped():
    client, sleep, _, _ = make_client(
        [
            httpx.Response(429, headers={"Retry-After": "600"}),
            httpx.Response(200, json={}),
        ]
    )
    client.get_blueprint("service")
    assert sleep.call_args.args[0] == 30.0


def test_5xx_uses_exponential_backoff_with_jitter():
    client, sleep, api_calls, _ = make_client(
        [
            httpx.Response(503),
            httpx.Response(502),
            httpx.Response(500),
            httpx.Response(200, json={}),
        ]
    )
    client.get_blueprint("service")
    waits = [c.args[0] for c in sleep.call_args_list]
    assert len(waits) == 3
    for wait, base in zip(waits, [0.5, 1.0, 2.0], strict=True):
        assert base <= wait <= base + 0.25  # base delay + up to 0.25 s jitter


def test_network_error_is_retried():
    client, sleep, api_calls, _ = make_client(
        [
            httpx.ConnectError("connection refused"),
            httpx.Response(200, json={}),
        ]
    )
    client.get_blueprint("service")
    assert len(api_calls()) == 2


def test_gives_up_after_max_attempts():
    client, sleep, api_calls, _ = make_client([httpx.Response(503)] * MAX_ATTEMPTS)
    with pytest.raises(PortApiError, match="gave up after 5 attempts"):
        client.get_blueprint("service")
    assert len(api_calls()) == MAX_ATTEMPTS
    assert sleep.call_count == MAX_ATTEMPTS - 1


@pytest.mark.parametrize("status", [400, 403, 404, 422])
def test_client_errors_fail_fast_without_retry(status):
    client, sleep, api_calls, _ = make_client([httpx.Response(status, json={"error": "bad"})])
    with pytest.raises(PortApiError) as err:
        client.upsert_entity("service", {"identifier": "x"})
    assert err.value.status_code == status
    assert len(api_calls()) == 1
    sleep.assert_not_called()


def test_token_is_fetched_once_and_reused():
    client, _, _, calls = make_client([httpx.Response(200, json={}), httpx.Response(200, json={})])
    client.get_blueprint("a")
    client.get_blueprint("b")
    token_calls = [c for c in calls if c.url.path.endswith("/auth/access_token")]
    assert len(token_calls) == 1
    assert calls[-1].headers["Authorization"] == "Bearer tok-1"


def test_expired_token_is_refreshed_once_on_401():
    client, _, api_calls, calls = make_client([httpx.Response(401), httpx.Response(200, json={"ok": True})])
    assert client.get_blueprint("service") == {"ok": True}
    token_calls = [c for c in calls if c.url.path.endswith("/auth/access_token")]
    assert len(token_calls) == 2  # first token + refresh
    assert len(api_calls()) == 2


def test_upsert_sends_upsert_and_merge_params():
    client, _, api_calls, _ = make_client([httpx.Response(201, json={"ok": True})])
    client.upsert_entity("service", {"identifier": "orders-api"})
    request = api_calls()[0]
    assert request.method == "POST"
    assert request.url.path == "/v1/blueprints/service/entities"
    assert request.url.params["upsert"] == "true" and request.url.params["merge"] == "true"


def test_parse_retry_after_formats():
    assert parse_retry_after("5") == 5.0
    assert parse_retry_after(None) is None
    assert parse_retry_after("not-a-date") is None
    assert parse_retry_after("Wed, 21 Oct 2015 07:28:00 GMT") == 0.0  # a date in the past = 0


def test_missing_credentials_are_rejected():
    with pytest.raises(ValueError):
        PortClient("", "")
