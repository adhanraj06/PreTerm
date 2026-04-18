from __future__ import annotations

from datetime import UTC


class YFinanceClient:
    def get_asset_context(self, ticker: str) -> dict[str, object] | None:
        try:
            import yfinance as yf
        except Exception:
            return None

        try:
            asset = yf.Ticker(ticker)
            history = asset.history(period="1mo", interval="1d", auto_adjust=False)
            fast_info = getattr(asset, "fast_info", None)
            info = getattr(asset, "info", {}) or {}
        except Exception:
            return None

        observations: list[dict[str, object]] = []
        if history is not None and not history.empty:
            for index, row in history.tail(20).iterrows():
                try:
                    close = float(row["Close"])
                except Exception:
                    continue
                observations.append(
                    {
                        "date": index.to_pydatetime().astimezone(UTC).date(),
                        "close": close,
                    }
                )

        latest_price = None
        previous_close = None
        currency = None
        market_cap = None
        exchange = None

        if fast_info is not None:
            latest_price = getattr(fast_info, "last_price", None)
            previous_close = getattr(fast_info, "previous_close", None)
            currency = getattr(fast_info, "currency", None)
            market_cap = getattr(fast_info, "market_cap", None)
            exchange = getattr(fast_info, "exchange", None)

        if latest_price is None:
            latest_price = info.get("currentPrice") or info.get("regularMarketPrice")
        if previous_close is None:
            previous_close = info.get("previousClose")
        if currency is None:
            currency = info.get("currency")
        if market_cap is None:
            market_cap = info.get("marketCap")
        if exchange is None:
            exchange = info.get("exchange")

        price_change = None
        if latest_price is not None and previous_close not in (None, 0):
            price_change = float(latest_price) - float(previous_close)

        return {
            "ticker": ticker,
            "name": info.get("shortName") or info.get("longName") or ticker,
            "latest_price": float(latest_price) if latest_price is not None else None,
            "price_change": price_change,
            "currency": currency,
            "market_cap": int(market_cap) if market_cap is not None else None,
            "exchange": exchange,
            "observations": observations,
        }
