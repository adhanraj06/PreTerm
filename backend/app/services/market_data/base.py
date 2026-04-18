from abc import ABC, abstractmethod

from app.schemas.market import MarketDetail, MarketListItem


class MarketDataProvider(ABC):
    @abstractmethod
    def list_markets(self) -> list[MarketListItem]:
        raise NotImplementedError

    @abstractmethod
    def get_market_by_id(self, market_id: int) -> MarketDetail | None:
        raise NotImplementedError
