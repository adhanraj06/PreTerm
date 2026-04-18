from datetime import date

from pydantic import BaseModel


class MacroObservationRead(BaseModel):
    date: date
    value: float


class MacroSeriesRead(BaseModel):
    series_id: str
    title: str
    units: str
    frequency: str
    latest_value: float | None = None
    previous_value: float | None = None
    change: float | None = None
    observations: list[MacroObservationRead]


class MacroContextResponse(BaseModel):
    available: bool
    reason: str | None = None
    market_id: int
    market_title: str
    series: list[MacroSeriesRead]
    macro_source: str | None = None
