from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WatchlistMarketSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    category: str
    status: str
    last_price: float
    probability_change: float


class WatchlistItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    market_id: int
    position: int | None = None
    notes: str | None = None
    created_at: datetime
    market: WatchlistMarketSummary


class WatchlistRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime
    updated_at: datetime
    items: list[WatchlistItemRead] = Field(default_factory=list)


class WatchlistCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class WatchlistItemCreate(BaseModel):
    market_id: int
    position: int | None = None
    notes: str | None = None
