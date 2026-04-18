import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class MarketSnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    captured_at: datetime
    price: float
    volume: int | None = None
    open_interest: int | None = None
    metadata_json: str | None = None

    @field_serializer("metadata_json")
    def serialize_metadata(self, value: str | None) -> Any:
        if not value:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value


class MarketTimelineEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    occurred_at: datetime
    move: float | None = None
    price_after_move: float | None = None
    reason: str
    linked_label: str | None = None
    linked_type: str | None = None
    linked_url: str | None = None
    metadata_json: str | None = None

    @field_serializer("metadata_json")
    def serialize_metadata(self, value: str | None) -> Any:
        if not value:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value


class MarketBriefRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    summary: str
    why_this_matters_now: str
    what_changed: str
    bull_case: str
    base_case: str
    bear_case: str
    catalysts: str
    drivers: str
    risks: str
    what_would_change_probability: str
    sources_json: str | None = None
    recent_headlines_json: str | None = None
    generated_at: datetime

    @field_serializer("sources_json")
    def serialize_sources(self, value: str | None) -> Any:
        if not value:
            return []
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return []

    @field_serializer("recent_headlines_json")
    def serialize_recent_headlines(self, value: str | None) -> Any:
        if not value:
            return []
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return []


class MarketListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: str | None = None
    source: str
    title: str
    slug: str
    category: str
    status: str
    close_time: datetime | None = None
    last_price: float
    probability_change: float
    volume: int | None = None
    open_interest: int | None = None
    description: str | None = None
    metadata_json: str | None = None
    brief: MarketBriefRead | None = None

    @field_serializer("metadata_json")
    def serialize_metadata(self, value: str | None) -> Any:
        if not value:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value


class MarketDetail(MarketListItem):
    snapshots: list[MarketSnapshotRead] = Field(default_factory=list)
    timeline_entries: list[MarketTimelineEntryRead] = Field(default_factory=list)
