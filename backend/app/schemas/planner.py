from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.watchlist import WatchlistMarketSummary


class PlannedEventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    date: date
    location: str | None = Field(default=None, max_length=160)
    concern_type: str = Field(min_length=1, max_length=80)
    notes: str | None = Field(default=None, max_length=1200)


class PlannedEventMarketSuggestion(BaseModel):
    market: WatchlistMarketSummary
    relevance_score: float
    rationale: str


class PlannedEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    date: date
    location: str | None = None
    concern_type: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    suggestions: list[PlannedEventMarketSuggestion] = Field(default_factory=list)
