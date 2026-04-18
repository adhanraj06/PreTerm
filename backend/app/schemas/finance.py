from datetime import date

from pydantic import BaseModel


class AssetObservationRead(BaseModel):
    date: date
    close: float


class AssetContextRead(BaseModel):
    ticker: str
    name: str
    latest_price: float | None = None
    price_change: float | None = None
    currency: str | None = None
    market_cap: int | None = None
    exchange: str | None = None
    observations: list[AssetObservationRead]


class EdgarFilingRead(BaseModel):
    form: str
    filing_date: date
    description: str
    document_url: str | None = None


class CompanyContextRead(BaseModel):
    company_name: str
    cik: str
    latest_filings: list[EdgarFilingRead]


class FinanceContextResponse(BaseModel):
    available: bool
    reason: str | None = None
    market_id: int
    market_title: str
    asset_context: AssetContextRead | None = None
    company_context: CompanyContextRead | None = None
    context_ticker: str | None = None
    context_kind: str | None = None


class EdgarBrowseResponse(BaseModel):
    available: bool
    reason: str | None = None
    ticker: str
    company_name: str
    cik: str
    filings: list[EdgarFilingRead]
