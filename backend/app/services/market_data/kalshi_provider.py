from __future__ import annotations

import hashlib
import json
import math
import time
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation

from sqlalchemy import Select, desc, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.integrations.kalshi_client import KalshiClient
from app.models.market import Market, MarketBrief, MarketSnapshot, MarketTimelineEntry
from app.schemas.market import MarketDetail, MarketListItem


def _base_market_query() -> Select[tuple[Market]]:
    return (
        select(Market)
        .options(
            selectinload(Market.brief),
            selectinload(Market.snapshots),
            selectinload(Market.timeline_entries),
        )
        .where(Market.source == "kalshi")
        .order_by(Market.category.asc(), desc(Market.last_price))
    )


def _parse_decimal(value: object, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    try:
        return float(Decimal(str(value)))
    except (InvalidOperation, ValueError, TypeError):
        return default


def _parse_int_from_fp(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(Decimal(str(value)))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _parse_dt(value: object) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


def _stable_market_slug(ticker: str, title: str) -> str:
    base = "-".join(title.lower().split())[:72].strip("-")
    return f"{base}-{ticker.lower()}" if base else ticker.lower()


def _normalize_status(value: str | None) -> str:
    if not value:
        return "open"
    return value.lower()


def _deterministic_external_number(external_id: str) -> int:
    digest = hashlib.sha256(external_id.encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def _brief_clip(text: str, max_len: int) -> str:
    cleaned = text.strip()
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 1].rstrip() + "…"


BRIEF_JSON_KEYS: tuple[str, ...] = (
    "summary",
    "why_this_matters_now",
    "what_changed",
    "bull_case",
    "base_case",
    "bear_case",
    "catalysts",
    "drivers",
    "risks",
    "what_would_change_probability",
)


def _yes_prices_from_market_payload(market_payload: dict[str, object]) -> tuple[float, float]:
    """Best-effort implied yes probability (0–1) from Kalshi list/get market payloads."""
    cur = _parse_decimal(market_payload.get("last_price_dollars"))
    prev = _parse_decimal(market_payload.get("previous_price_dollars"), 0.0)

    if cur <= 0:
        bid = _parse_decimal(market_payload.get("yes_bid_dollars"))
        ask = _parse_decimal(market_payload.get("yes_ask_dollars"))
        if bid > 0 and ask > 0:
            cur = (bid + ask) / 2.0
        elif bid > 0:
            cur = bid
        elif ask > 0:
            cur = ask

    if cur <= 0:
        lp = market_payload.get("last_price")
        if isinstance(lp, (int, float)):
            v = float(lp)
            if 0 < v <= 1:
                cur = v
            elif 1 < v <= 100:
                cur = v / 100.0
        elif isinstance(lp, str):
            cur = _parse_decimal(lp)

    if prev <= 0 and cur > 0:
        prev = cur
    if cur <= 0 and prev > 0:
        cur = prev

    cur = max(0.0, min(1.0, cur))
    prev = max(0.0, min(1.0, prev if prev > 0 else cur))
    return cur, prev


def _merge_gemini_brief_if_enabled(
    fields: dict[str, str],
    *,
    title: str,
    rules_excerpt: str,
    pct: int,
    delta_pts: float,
) -> dict[str, str]:
    if not settings.kalshi_brief_use_gemini or not settings.gemini_api_key:
        return fields
    try:
        from app.integrations.gemini_client import GeminiClient

        client = GeminiClient(api_key=settings.gemini_api_key, model=settings.gemini_model)
        system = (
            "Expand notes for a Kalshi binary contract. Rules: neutral tone, no metaphors, no 'you/we', "
            "no slogans. Do NOT paste or quote Kalshi rule text verbatim; at most refer to 'Kalshi’s posted rules'. "
            "Avoid boilerplate such as 'last trade vs prior reference, volume, spread' or 'Middle: X% is a working level'. "
            "Each field is 1–3 short factual sentences tied to this contract. "
            f"Return ONLY JSON with these string keys: {list(BRIEF_JSON_KEYS)}."
        )
        payload = {
            "contract_title": title,
            "implied_yes_percent": pct,
            "change_vs_prior_reference_percentage_points": round(delta_pts, 2),
            "rules_excerpt": rules_excerpt[:700],
            "draft": {k: fields[k] for k in BRIEF_JSON_KEYS},
        }
        raw = client.generate_json_text_sync(system, json.dumps(payload, indent=2))
        merged = json.loads(raw)
        out = dict(fields)
        for k in BRIEF_JSON_KEYS:
            val = merged.get(k)
            if isinstance(val, str) and val.strip():
                out[k] = val.strip()
        return out
    except Exception:
        return fields


def _build_brief(event: dict[str, object], market: dict[str, object], current_probability: float, move_points: float) -> dict[str, str]:
    event_title = str(event.get("title") or market.get("title") or "Contract")
    rules_primary = str(market.get("rules_primary") or "").strip()
    rules_secondary = str(market.get("rules_secondary") or "").strip()
    strike_date = str(event.get("strike_date") or market.get("close_time") or "resolution")
    category = str(event.get("category") or "kalshi").lower()
    move_abs = abs(round(move_points, 1))
    pct = round(current_probability * 100)
    lean = "above" if current_probability >= 0.5 else "below"
    vol = _parse_int_from_fp(market.get("volume_fp"))
    oi = _parse_int_from_fp(market.get("open_interest_fp"))

    summary = f"{event_title}: last Kalshi implied yes near {pct}% ({lean} 50%)."
    why_now = (
        f"Kalshi binary on {event_title}; price is the traded estimate of a \"yes\" under the posted rules through {strike_date}."
    )
    if move_abs < 0.25:
        what_changed = "Little change versus the prior reference print on Kalshi."
    else:
        direction = "up" if move_points >= 0 else "down"
        what_changed = f"Versus the prior reference, implied yes moved {direction} ~{move_abs:g} percentage points."

    bull_case = (
        f"Upside: information into {strike_date} supports a clean \"yes\" under the rule text; {pct}% understates that path."
    )
    base_case = (
        f"Baseline: ~{pct}% is the current consensus implied yes; it should drift only when dated, settlement-relevant facts move."
    )
    bear_case = (
        f"Downside: facts or timing undermine a \"yes\" for {event_title}; repricing toward lower implied yes."
    )
    catalysts = (
        "Settlement-relevant primary inputs—official results, certified stats, deadlines, and eligibility outcomes—"
        "rather than commentary or unverified posts. Full wording lives in Kalshi’s posted rules for this market."
    )
    if vol:
        drivers = f"Recent Kalshi print shows roughly {vol:,} contracts traded"
        if oi:
            drivers += f" and about {oi:,} open interest"
        drivers += "."
    elif oi:
        drivers = f"Open interest is about {oi:,} contracts; volume on this refresh is light or not surfaced."
    else:
        drivers = f"{category} flow on Kalshi into {strike_date}; liquidity can gap around headline catalysts."
    risks = "Resolution wording, calendar slippage, thin liquidity, correlated shocks."
    change_probability = "Moves on official inputs that change the resolution facts, rule clarifications, or large related markets."

    sources = [
        {"label": "Kalshi market data", "type": "market"},
        {"label": "Kalshi event metadata", "type": "event"},
    ]
    if rules_primary:
        sources.append({"label": "Kalshi rules_primary", "type": "rules"})
    if rules_secondary:
        sources.append({"label": "Kalshi rules_secondary", "type": "rules"})

    return {
        "summary": summary,
        "why_this_matters_now": why_now,
        "what_changed": what_changed,
        "bull_case": bull_case,
        "base_case": base_case,
        "bear_case": bear_case,
        "catalysts": catalysts,
        "drivers": drivers,
        "risks": risks,
        "what_would_change_probability": change_probability,
        "sources_json": json.dumps(sources),
        "recent_headlines_json": json.dumps([]),
    }


def _snapshot_meta_kind(metadata_json: str | None) -> str | None:
    if not metadata_json:
        return None
    try:
        return json.loads(metadata_json).get("kind")
    except json.JSONDecodeError:
        return None


def _all_snapshots_illustrative(ordered: list[MarketSnapshot]) -> bool:
    if len(ordered) < 2:
        return False
    return all(_snapshot_meta_kind(s.metadata_json) == "illustrative_path" for s in ordered)


def _illustrative_snapshots(
    ticker: str,
    previous_probability: float,
    current_probability: float,
    volume: int | None,
    open_interest: int | None,
    *,
    session_days: float = 6.5,
    steps: int = 16,
) -> list[MarketSnapshot]:
    """Multi-point path for charting when daily candles are off — anchored to Kalshi prior/last prints."""
    seed = _deterministic_external_number(ticker)
    start = float(previous_probability)
    end = float(current_probability)
    spread = abs(end - start)
    now = datetime.now(UTC)
    start_at = now - timedelta(days=session_days)
    span_s = max(1.0, session_days * 86400.0)
    out: list[MarketSnapshot] = []
    for i in range(steps):
        frac = i / (steps - 1) if steps > 1 else 0.0
        captured = start_at + timedelta(seconds=frac * span_s)
        if i == 0:
            price = start
        elif i == steps - 1:
            price = end
        else:
            u = frac * frac * (3.0 - 2.0 * frac)
            baseline = start + (end - start) * u
            envelope = 1.0 - (2.0 * frac - 1.0) ** 2
            flat = spread < 0.04
            amp = (0.11 if flat else 0.024) * envelope
            wave = amp * math.sin(frac * math.pi * 2.15 + (seed % 997) * 0.011)
            price = baseline + wave
            price = max(0.02, min(0.98, price))
        out.append(
            MarketSnapshot(
                captured_at=captured,
                price=round(price, 6),
                volume=volume,
                open_interest=open_interest,
                metadata_json=json.dumps(
                    {
                        "source": "kalshi",
                        "kind": "illustrative_path",
                        "note": "Modeled between previous_price and last_price for UI charting",
                    }
                ),
            )
        )
    return out


def _build_timeline_entries(snapshots: Iterable[MarketSnapshot], title: str) -> list[MarketTimelineEntry]:
    ordered = sorted(snapshots, key=lambda snapshot: snapshot.captured_at)
    if len(ordered) < 2:
        return []

    if _all_snapshots_illustrative(ordered):
        first, last = ordered[0], ordered[-1]
        move = round(last.price - first.price, 4)
        direction = "higher" if move >= 0 else "lower"
        pts = abs(round(move * 100, 1))
        return [
            MarketTimelineEntry(
                occurred_at=last.captured_at,
                move=move,
                price_after_move=last.price,
                reason=(
                    f"Implied yes {direction} ~{pts:g} pts from prior reference to last print on {title} "
                    f"(smoothed chart path; not exchange OHLC)."
                ),
                linked_label="Price track",
                linked_type="market_data",
                linked_url=None,
                metadata_json=json.dumps({"source": "kalshi", "kind": "illustrative_summary"}),
            )
        ]

    timeline_entries: list[MarketTimelineEntry] = []
    for previous, current in zip(ordered, ordered[1:], strict=False):
        move = round(current.price - previous.price, 4)
        direction = "higher" if move >= 0 else "lower"
        pts = abs(round(move * 100, 1))
        timeline_entries.append(
            MarketTimelineEntry(
                occurred_at=current.captured_at,
                move=move,
                price_after_move=current.price,
                reason=(
                    f"Kalshi daily close stepped {title} {direction}: implied yes moved ~{pts:g} pts between candle prints "
                    f"as the book repriced resolution odds."
                ),
                linked_label="Kalshi daily candle",
                linked_type="market_data",
                linked_url=None,
                metadata_json=json.dumps({"source": "kalshi", "kind": "candle_step"}),
            )
        )
    return timeline_entries


class KalshiMarketDataProvider:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.client = KalshiClient()

    def refresh(self) -> None:
        market_payloads = self.client.get_markets()
        seen_tickers: set[str] = set()
        event_cache: dict[str, dict[str, object]] = {}

        for payload in market_payloads:
            ticker = str(payload.get("ticker") or "")
            if not ticker or ticker in seen_tickers:
                continue
            seen_tickers.add(ticker)

            event_ticker = str(payload.get("event_ticker") or "")
            if event_ticker and event_ticker not in event_cache:
                event_cache[event_ticker] = self.client.get_event(event_ticker)

            event_payload = event_cache.get(event_ticker, {})
            self._upsert_market(payload, event_payload)

        self.db.commit()

    def list_markets(self) -> list[MarketListItem]:
        statement = _base_market_query()
        return [MarketListItem.model_validate(market) for market in self.db.scalars(statement).all()]

    def get_market_by_id(self, market_id: int) -> MarketDetail | None:
        statement = _base_market_query().where(Market.id == market_id)
        market = self.db.scalar(statement)
        return MarketDetail.model_validate(market) if market else None

    def _upsert_market(
        self,
        market_payload: dict[str, object],
        event_payload: dict[str, object],
    ) -> None:
        ticker = str(market_payload.get("ticker") or "")
        if not ticker:
            return

        event_ticker = str(market_payload.get("event_ticker") or "")

        statement = select(Market).where(Market.source == "kalshi", Market.external_id == ticker)
        market = self.db.scalar(statement)
        if market is None:
            market = Market(source="kalshi", external_id=ticker)
            self.db.add(market)

        current_probability, previous_probability = _yes_prices_from_market_payload(market_payload)
        probability_change = round(current_probability - previous_probability, 4)

        event_title = str(event_payload.get("title") or market_payload.get("title") or ticker)
        category = str(event_payload.get("category") or "kalshi").lower()

        market.title = str(market_payload.get("title") or event_title)
        market.slug = _stable_market_slug(ticker, market.title)
        market.category = category
        market.status = _normalize_status(str(market_payload.get("status") or "open"))
        market.close_time = _parse_dt(market_payload.get("close_time"))
        market.last_price = current_probability
        market.probability_change = probability_change
        market.volume = _parse_int_from_fp(market_payload.get("volume_fp"))
        market.open_interest = _parse_int_from_fp(market_payload.get("open_interest_fp"))
        market.description = str(
            event_payload.get("sub_title")
            or market_payload.get("subtitle")
            or f"Live Kalshi market for {event_title}."
        )
        market.metadata_json = json.dumps(
            {
                "provider": "kalshi",
                "market_ticker": ticker,
                "event_ticker": event_ticker,
                "series_ticker": event_payload.get("series_ticker"),
                "rules_primary": market_payload.get("rules_primary"),
                "rules_secondary": market_payload.get("rules_secondary"),
                "yes_bid_dollars": market_payload.get("yes_bid_dollars"),
                "yes_ask_dollars": market_payload.get("yes_ask_dollars"),
                "deterministic_external_number": _deterministic_external_number(ticker),
            }
        )

        snapshots = self._build_snapshots(event_payload, market_payload)
        market.snapshots = snapshots
        market.timeline_entries = _build_timeline_entries(snapshots, market.title)

        brief_fields = _build_brief(event_payload, market_payload, current_probability, probability_change * 100)
        brief_fields = _merge_gemini_brief_if_enabled(
            brief_fields,
            title=event_title,
            rules_excerpt=str(market_payload.get("rules_primary") or ""),
            pct=round(current_probability * 100),
            delta_pts=probability_change * 100,
        )
        if market.brief is None:
            market.brief = MarketBrief(**brief_fields)
        else:
            for key, value in brief_fields.items():
                setattr(market.brief, key, value)
            market.brief.generated_at = datetime.now(UTC)

    def _build_snapshots(
        self,
        event_payload: dict[str, object],
        market_payload: dict[str, object],
    ) -> list[MarketSnapshot]:
        ticker = str(market_payload.get("ticker") or "")
        series_ticker = str(event_payload.get("series_ticker") or "")
        candlesticks: list[dict[str, object]] = []
        if settings.kalshi_fetch_candlesticks_on_refresh and series_ticker and ticker:
            time.sleep(max(0.0, settings.kalshi_candlestick_delay_seconds))
            candlesticks = self.client.get_market_candlesticks(series_ticker, ticker)

        snapshots: list[MarketSnapshot] = []
        for candlestick in candlesticks:
            end_ts = candlestick.get("end_period_ts")
            if not isinstance(end_ts, int):
                continue
            captured_at = datetime.fromtimestamp(end_ts, tz=UTC)
            price = _parse_decimal((candlestick.get("price") or {}).get("close_dollars"))
            volume = _parse_int_from_fp(candlestick.get("volume_fp"))
            open_interest = _parse_int_from_fp(candlestick.get("open_interest_fp"))
            metadata = {
                "source": "kalshi",
                "kind": "kalshi_candle",
                "low_dollars": (candlestick.get("price") or {}).get("low_dollars"),
                "high_dollars": (candlestick.get("price") or {}).get("high_dollars"),
                "mean_dollars": (candlestick.get("price") or {}).get("mean_dollars"),
            }
            snapshots.append(
                MarketSnapshot(
                    captured_at=captured_at,
                    price=price,
                    volume=volume,
                    open_interest=open_interest,
                    metadata_json=json.dumps(metadata),
                )
            )

        if snapshots:
            return snapshots

        current_probability, previous_probability = _yes_prices_from_market_payload(market_payload)
        vol = _parse_int_from_fp(market_payload.get("volume_fp"))
        oi = _parse_int_from_fp(market_payload.get("open_interest_fp"))
        return _illustrative_snapshots(ticker, previous_probability, current_probability, vol, oi)
