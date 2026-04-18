import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_serializer


class SavedViewCreate(BaseModel):
    name: str
    layout_json: dict[str, Any] | None = None
    filters_json: dict[str, Any] | None = None


class SavedViewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    layout_json: str | None = None
    filters_json: str | None = None
    created_at: datetime
    updated_at: datetime

    @field_serializer("layout_json", "filters_json")
    def serialize_json_fields(self, value: str | None) -> Any:
        if not value:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
