from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Any

import httpx

from omi_cli.config import Config

USER_AGENT = "omi-cli/0.1.0"
MAX_RETRIES = 3
BACKOFF_BASE = 1.0


class OmiError(Exception):
    def __init__(self, status: int, detail: Any, request: httpx.Request) -> None:
        self.status = status
        self.detail = detail
        super().__init__(f"HTTP {status} on {request.method} {request.url.path}: {detail}")


class OmiClient:
    def __init__(self, config: Config, *, timeout: float = 30.0) -> None:
        self._config = config
        self._http = httpx.Client(
            base_url=config.base_url,
            headers={"User-Agent": USER_AGENT, **config.auth_header},
            timeout=timeout,
        )

    def __enter__(self) -> OmiClient:
        return self

    def __exit__(self, *_: object) -> None:
        self._http.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
    ) -> Any:
        clean_params = {k: v for k, v in (params or {}).items() if v is not None}
        attempt = 0
        while True:
            attempt += 1
            try:
                response = self._http.request(method, path, params=clean_params or None, json=json)
            except (httpx.TransportError, httpx.TimeoutException):
                if attempt >= MAX_RETRIES:
                    raise
                time.sleep(BACKOFF_BASE * 2 ** (attempt - 1))
                continue

            if response.status_code == 429 and attempt < MAX_RETRIES:
                time.sleep(_retry_after(response, attempt))
                continue
            if 500 <= response.status_code < 600 and attempt < MAX_RETRIES:
                time.sleep(BACKOFF_BASE * 2 ** (attempt - 1))
                continue

            if response.status_code >= 400:
                try:
                    detail = response.json()
                except Exception:
                    detail = response.text
                raise OmiError(response.status_code, detail, response.request)
            if response.status_code == 204 or not response.content:
                return None
            return response.json()

    def get(self, path: str, **params: Any) -> Any:
        return self.request("GET", path, params=params)

    def post(self, path: str, json: Any | None = None, **params: Any) -> Any:
        return self.request("POST", path, params=params, json=json)

    def patch(self, path: str, json: Any | None = None) -> Any:
        return self.request("PATCH", path, json=json)

    def delete(self, path: str) -> Any:
        return self.request("DELETE", path)

    def paginate(
        self,
        path: str,
        *,
        page_size: int = 100,
        max_items: int | None = None,
        **params: Any,
    ) -> Iterator[dict[str, Any]]:
        offset = 0
        yielded = 0
        while True:
            page = self.get(path, limit=page_size, offset=offset, **params)
            if not isinstance(page, list) or not page:
                return
            for item in page:
                yield item
                yielded += 1
                if max_items and yielded >= max_items:
                    return
            if len(page) < page_size:
                return
            offset += page_size


def _retry_after(response: httpx.Response, attempt: int) -> float:
    header = response.headers.get("Retry-After") or response.headers.get("X-RateLimit-Reset")
    if header:
        try:
            return max(1.0, float(header))
        except ValueError:
            pass
    return BACKOFF_BASE * 2 ** (attempt - 1)
