from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta

import httpx

from app.core.config import settings


class KalshiClient:
    def __init__(self) -> None:
        self.base_url = settings.kalshi_api_base.rstrip("/")
        self.timeout = settings.kalshi_request_timeout_seconds

    def _get(self, path: str, params: dict[str, object] | None = None) -> dict[str, object]:
        delay = 0.35
        last_response: httpx.Response | None = None
        max_attempts = max(1, settings.kalshi_max_429_retries)

        for attempt in range(max_attempts):
            with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
                response = client.get(path, params=params)
            last_response = response

            if response.status_code == 429 and attempt < max_attempts - 1:
                retry_after = response.headers.get("Retry-After")
                if retry_after:
                    try:
                        time.sleep(min(float(retry_after), 8.0))
                    except ValueError:
                        time.sleep(delay)
                else:
                    time.sleep(delay)
                delay = min(delay * 1.55, 6.0)
                continue

            response.raise_for_status()
            return response.json()

        if last_response is not None:
            last_response.raise_for_status()
        return {}

    def get_markets(self) -> list[dict[str, object]]:
        if settings.kalshi_series_filter:
            markets: list[dict[str, object]] = []
            for series_ticker in settings.kalshi_series_filter:
                payload = self._get(
                    "/markets",
                    params={
                        "series_ticker": series_ticker,
                        "status": settings.kalshi_market_status,
                        "limit": settings.kalshi_market_limit,
                        "mve_filter": "exclude",
                    },
                )
                markets.extend(payload.get("markets", []))
            return markets[: settings.kalshi_market_limit]

        payload = self._get(
            "/markets",
            params={
                "status": settings.kalshi_market_status,
                "limit": settings.kalshi_market_limit,
                "mve_filter": "exclude",
            },
        )
        return payload.get("markets", [])

    def get_event(self, event_ticker: str) -> dict[str, object]:
        payload = self._get(f"/events/{event_ticker}", params={"with_nested_markets": "false"})
        return payload.get("event", {})

    def get_market_candlesticks(self, series_ticker: str, market_ticker: str) -> list[dict[str, object]]:
        end_ts = int(datetime.now(UTC).timestamp())
        start_ts = int((datetime.now(UTC) - timedelta(days=7)).timestamp())
        try:
            payload = self._get(
                f"/series/{series_ticker}/markets/{market_ticker}/candlesticks",
                params={
                    "start_ts": start_ts,
                    "end_ts": end_ts,
                    "period_interval": 1440,
                    "include_latest_before_start": "true",
                },
            )
        except httpx.HTTPStatusError:
            return []
        return payload.get("candlesticks", [])
