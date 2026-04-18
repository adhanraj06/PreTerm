from pydantic import BaseModel

from app.schemas.finance import AssetContextRead


class MacroCatalogItem(BaseModel):
    key: str
    title: str


class ResearchQuoteResponse(BaseModel):
    available: bool
    reason: str | None = None
    asset: AssetContextRead | None = None
