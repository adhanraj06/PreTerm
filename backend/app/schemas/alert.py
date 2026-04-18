import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_serializer


class AlertPreferenceCreate(BaseModel):
    market_id: int | None = None
    rule_type: str
    threshold_value: float | None = None
    enabled: bool = True


class AlertPreferenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    market_id: int | None = None
    rule_type: str
    threshold_value: float | None = None
    enabled: bool
    created_at: datetime
    updated_at: datetime


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    alert_preference_id: int | None = None
    market_id: int | None = None
    kind: str
    title: str
    message: str
    is_read: bool
    created_at: datetime
    metadata_json: str | None = None

    @field_serializer("metadata_json")
    def decode_metadata(self, value: str | None) -> Any:
        if not value:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
