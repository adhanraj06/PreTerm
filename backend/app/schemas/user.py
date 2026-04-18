from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_serializer


class UserProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bio: str | None = None
    avatar_url: str | None = None
    default_market_focus: str | None = None
    timezone: str | None = None
    theme: str | None = None


class UserPreferenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    preferred_categories: str
    preferred_desk_mode: str | None = None
    alert_move_threshold: int | None = None
    alert_headline_matches: bool
    created_at: datetime
    updated_at: datetime

    @field_serializer("preferred_categories")
    def serialize_preferred_categories(self, value: str) -> Any:
        import json

        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return []


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    display_name: str
    created_at: datetime
    updated_at: datetime
    profile: UserProfileRead
    preference: UserPreferenceRead
