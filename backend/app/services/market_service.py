from sqlalchemy.orm import Session

from app.schemas.market import MarketDetail, MarketListItem
from app.services.market_data import get_market_data_provider


def list_markets(db: Session) -> list[MarketListItem]:
    """Return market overviews from the configured data provider."""
    provider = get_market_data_provider(db)
    return provider.list_markets()


def get_market_by_id(db: Session, market_id: int) -> MarketDetail | None:
    """Return a single market detail record with provider-backed history and brief data."""
    provider = get_market_data_provider(db)
    return provider.get_market_by_id(market_id)
