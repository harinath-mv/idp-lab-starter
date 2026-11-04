"""Day 20: PortClient.search_entities walks every page and stops safely."""

from unittest.mock import Mock

import httpx
import pytest

from app.port_client import PortApiError, PortClient

TOKEN_OK = httpx.Response(200, json={"accessToken": "tok-1", "expiresIn": 3600})


def make_client(pages: list[dict]):
    """Port that returns `pages` in order for search calls; records each request body."""
    bodies = []
    queue = list(pages)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/auth/access_token"):
            return TOKEN_OK
        bodies.append(httpx.Request("POST", "x", content=request.content).read())
        return httpx.Response(200, json=queue.pop(0))

    http = httpx.Client(base_url="https://api.port.io/v1", transport=httpx.MockTransport(handler))
    return PortClient("id", "secret", http=http, sleep=Mock()), bodies


def test_reads_all_pages_in_order():
    client, bodies = make_client(
        [
            {"entities": [{"identifier": "a"}, {"identifier": "b"}], "next": "t1"},
            {"entities": [{"identifier": "c"}, {"identifier": "d"}], "next": "t2"},
            {"entities": [{"identifier": "e"}]},  # no "next" = last page
        ]
    )
    ids = [e["identifier"] for e in client.search_entities("service", page_size=2)]
    assert ids == ["a", "b", "c", "d", "e"]
    assert len(bodies) == 3
    assert b'"from"' not in bodies[0]  # first page has no token
    assert b'"from":"t1"' in bodies[1].replace(b" ", b"")
    assert b'"from":"t2"' in bodies[2].replace(b" ", b"")


def test_single_page():
    client, bodies = make_client([{"entities": [{"identifier": "only"}], "next": None}])
    assert [e["identifier"] for e in client.search_entities("service")] == ["only"]
    assert len(bodies) == 1


def test_empty_blueprint():
    client, _ = make_client([{"entities": []}])
    assert list(client.search_entities("service")) == []


def test_pages_are_fetched_lazily():
    """A generator only asks for the next page when you need it (saves calls and memory)."""
    client, bodies = make_client(
        [
            {"entities": [{"identifier": "a"}], "next": "t1"},
            {"entities": [{"identifier": "b"}]},
        ]
    )
    first = next(client.search_entities("service", page_size=1))
    assert first["identifier"] == "a"
    assert len(bodies) == 1


def test_stuck_token_hits_the_safety_stop():
    client, _ = make_client([{"entities": [{"identifier": "x"}], "next": "same"}] * 3)
    with pytest.raises(PortApiError, match="stopped after 3 pages"):
        list(client.search_entities("service", max_pages=3))
