from __future__ import annotations

import pytest

from omi_cli.client import OmiClient, OmiError
from omi_cli.config import Config


def test_bearer_header_is_set(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url="https://api.omi.me/v1/dev/keys",
        json=[],
    )
    with OmiClient(Config(api_key="omi_dev_abc", base_url="https://api.omi.me")) as c:
        c.get("/v1/dev/keys")
    request = httpx_mock.get_request()
    assert request.headers["Authorization"] == "Bearer omi_dev_abc"
    assert request.headers["User-Agent"].startswith("omi-cli/")


def test_4xx_raises_omi_error(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url="https://api.omi.me/v1/dev/keys",
        status_code=401,
        json={"detail": "Invalid authentication credentials"},
    )
    with (
        OmiClient(Config(api_key="bad", base_url="https://api.omi.me")) as c,
        pytest.raises(OmiError) as excinfo,
    ):
        c.get("/v1/dev/keys")
    assert excinfo.value.status == 401
    assert "Invalid authentication credentials" in str(excinfo.value)


def test_429_retries_then_succeeds(httpx_mock, monkeypatch):
    monkeypatch.setattr("omi_cli.client.time.sleep", lambda *_: None)
    httpx_mock.add_response(
        method="GET",
        url="https://api.omi.me/v1/dev/keys",
        status_code=429,
        headers={"Retry-After": "1"},
        json={"detail": "rate limited"},
    )
    httpx_mock.add_response(
        method="GET",
        url="https://api.omi.me/v1/dev/keys",
        json=[{"id": "k1"}],
    )
    with OmiClient(Config(api_key="x", base_url="https://api.omi.me")) as c:
        data = c.get("/v1/dev/keys")
    assert data == [{"id": "k1"}]


def test_paginate_stops_on_short_page(httpx_mock):
    httpx_mock.add_response(
        url="https://api.omi.me/v1/dev/user/memories?limit=2&offset=0",
        json=[{"id": "a"}, {"id": "b"}],
    )
    httpx_mock.add_response(
        url="https://api.omi.me/v1/dev/user/memories?limit=2&offset=2",
        json=[{"id": "c"}],
    )
    with OmiClient(Config(api_key="x", base_url="https://api.omi.me")) as c:
        items = list(c.paginate("/v1/dev/user/memories", page_size=2))
    assert [m["id"] for m in items] == ["a", "b", "c"]


def test_paginate_honors_max_items(httpx_mock):
    httpx_mock.add_response(
        url="https://api.omi.me/v1/dev/user/memories?limit=10&offset=0",
        json=[{"id": str(i)} for i in range(10)],
    )
    with OmiClient(Config(api_key="x", base_url="https://api.omi.me")) as c:
        items = list(c.paginate("/v1/dev/user/memories", page_size=10, max_items=3))
    assert len(items) == 3
