from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import Select, desc, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.market import Market
from app.schemas.market import MarketDetail, MarketListItem
from app.services.market_data.base import MarketDataProvider
from app.services.market_data.kalshi_provider import KalshiMarketDataProvider


_last_kalshi_refresh: datetime | None = None


def _base_market_query(source: str) -> Select[tuple[Market]]:
    return (
        select(Market)
        .options(
            selectinload(Market.brief),
            selectinload(Market.snapshots),
            selectinload(Market.timeline_entries),
        )
        .where(Market.source == source)
        .order_by(Market.category.asc(), desc(Market.last_price))
    )


class SeededMarketDataProvider(MarketDataProvider):
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_markets(self) -> list[MarketListItem]:
        statement = _base_market_query("seed")
        return [MarketListItem.model_validate(market) for market in self.db.scalars(statement).all()]

    def get_market_by_id(self, market_id: int) -> MarketDetail | None:
        statement = _base_market_query("seed").where(Market.id == market_id)
        market = self.db.scalar(statement)
        return MarketDetail.model_validate(market) if market else None


class FallbackMarketDataProvider(MarketDataProvider):
    def __init__(self, primary: MarketDataProvider, fallback: MarketDataProvider) -> None:
        self.primary = primary
        self.fallback = fallback

    def list_markets(self) -> list[MarketListItem]:
        markets = self.primary.list_markets()
        return markets if markets else self.fallback.list_markets()

    def get_market_by_id(self, market_id: int) -> MarketDetail | None:
        market = self.primary.get_market_by_id(market_id)
        return market if market is not None else self.fallback.get_market_by_id(market_id)


def _kalshi_provider_needs_refresh() -> bool:
    if _last_kalshi_refresh is None:
        return True
    threshold = timedelta(seconds=settings.market_data_refresh_seconds)
    return datetime.now(UTC) - _last_kalshi_refresh >= threshold


def _mark_kalshi_refreshed() -> None:
    global _last_kalshi_refresh
    _last_kalshi_refresh = datetime.now(UTC)


def get_market_data_provider(db: Session) -> MarketDataProvider:
    seeded_provider = SeededMarketDataProvider(db)

    if settings.market_data_provider.lower() != "kalshi":
        return seeded_provider

    kalshi_provider = KalshiMarketDataProvider(db)
    if _kalshi_provider_needs_refresh():
        try:
            kalshi_provider.refresh()
            _mark_kalshi_refreshed()
        except Exception:
            if not settings.kalshi_fallback_to_seeded:
                raise

    if settings.kalshi_fallback_to_seeded:
        return FallbackMarketDataProvider(kalshi_provider, seeded_provider)

    return kalshi_provider
