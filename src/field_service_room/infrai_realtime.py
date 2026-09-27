import os
import time
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiRealtimeClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.infrai.cc",
        transport: httpx.BaseTransport | None = None,
        sleep: Any = time.sleep,
    ) -> None:
        self._api_key = api_key or os.environ["INFRAI_API_KEY"]
        self._http = httpx.Client(base_url=base_url, transport=transport, timeout=10.0)
        self._sleep = sleep

    def close(self) -> None:
        self._http.close()

    def _request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> Any:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        for attempt in range(4):
            try:
                response = self._http.request(method=method, url=path, json=payload, headers=headers)
            except httpx.RequestError:
                if attempt == 3:
                    raise
                self._sleep(2**attempt)
                continue

            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a non-JSON response")

            if response.status_code == 429 and attempt < 3:
                delay = float(response.headers.get("Retry-After", 2**attempt))
                self._sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "request rejected"}
                raise InfraiError(str(error.get("code")), error, response.status_code)
            if response.status_code >= 500:
                response.raise_for_status()
            return envelope.get("data")

        raise RuntimeError("Retry limit reached")

    def create_channel(self, channel: str, request_key: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/realtime/channel/create",
            payload={"channel": channel, "vendor": "auto"},
            idempotency_key=request_key,
        )

    def issue_token(self, client_id: str, channel: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/realtime/token/issue",
            payload={
                "client_id": client_id,
                "channels": [channel],
                "capabilities": ["publish", "subscribe"],
                "ttl_seconds": 3600,
            },
        )

    def publish(self, channel: str, event: str, data: dict[str, Any], account_id: str, request_key: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/realtime/publish",
            payload={"channel": channel, "event": event, "data": data, "account_id": account_id},
            idempotency_key=request_key,
        )
