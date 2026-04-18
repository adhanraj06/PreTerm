from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.core.config import settings
from app.integrations.edgar_client import EdgarClient
from app.integrations.yfinance_client import YFinanceClient
from app.models.market import Market
from app.schemas.finance import (
    AssetContextRead,
    CompanyContextRead,
    EdgarFilingRead,
    FinanceContextResponse,
)
from app.services.market_service import get_market_by_id


MARKET_FINANCE_MAP: dict[str, dict[str, str]] = {
    "nvidia-next-quarter-revenue-beat": {"ticker": "NVDA", "kind": "company"},
    "tesla-next-quarter-deliveries-above-consensus": {"ticker": "TSLA", "kind": "company"},
    "amazon-operating-margin-expand-next-quarter": {"ticker": "AMZN", "kind": "company"},
    "microsoft-cloud-growth-above-30-next-quarter": {"ticker": "MSFT", "kind": "company"},
    "alphabet-search-revenue-beat-next-quarter": {"ticker": "GOOGL", "kind": "company"},
    "meta-reality-labs-loss-narrow-q3-2026": {"ticker": "META", "kind": "company"},
    "sp500-close-above-6000-by-august-2026": {"ticker": "^GSPC", "kind": "index"},
    "bitcoin-new-all-time-high-by-december-2026": {"ticker": "BTC-USD", "kind": "crypto"},
    "spot-eth-etf-flows-positive-q3-2026": {"ticker": "ETH-USD", "kind": "crypto"},
    "sol-above-200-before-october-2026": {"ticker": "SOL-USD", "kind": "crypto"},
    "crude-wti-above-85-by-september-2026": {"ticker": "CL=F", "kind": "commodity"},
    "gold-futures-above-3200-by-december-2026": {"ticker": "GC=F", "kind": "commodity"},
}


def get_finance_context(db: Session, market_id: int) -> FinanceContextResponse | None:
    market = get_market_by_id(db, market_id)
    if market is None:
        return None

    orm_market = db.get(Market, market_id)
    if orm_market is None:
        return None

    mapping = MARKET_FINANCE_MAP.get(orm_market.slug)
    if mapping is None:
        return FinanceContextResponse(
            available=False,
            reason="No company or asset context is configured for this market.",
            market_id=market.id,
            market_title=market.title,
            context_ticker=None,
            context_kind=None,
        )

    asset_context = None
    company_context = None
    failure_reasons: list[str] = []

    if settings.enable_yfinance:
        raw_asset = YFinanceClient().get_asset_context(mapping["ticker"])
        if raw_asset is not None:
            asset_context = AssetContextRead.model_validate(raw_asset)
        else:
            failure_reasons.append("Yahoo Finance (yfinance) context unavailable")

    if settings.enable_edgar and mapping["kind"] == "company":
        raw_company = EdgarClient().get_company_context(mapping["ticker"])
        if raw_company is not None:
            company_context = CompanyContextRead(
                company_name=str(raw_company.get("company_name") or mapping["ticker"]),
                cik=str(raw_company.get("cik") or ""),
                latest_filings=[
                    EdgarFilingRead.model_validate(filing)
                    for filing in raw_company.get("latest_filings", [])
                ],
            )
        else:
            failure_reasons.append("SEC EDGAR context unavailable")

    if asset_context is None and company_context is None:
        return FinanceContextResponse(
            available=False,
            reason=", ".join(failure_reasons) if failure_reasons else "Finance context unavailable.",
            market_id=market.id,
            market_title=market.title,
            context_ticker=mapping["ticker"],
            context_kind=mapping["kind"],
        )

    return FinanceContextResponse(
        available=True,
        market_id=market.id,
        market_title=market.title,
        asset_context=asset_context,
        company_context=company_context,
        context_ticker=mapping["ticker"],
        context_kind=mapping["kind"],
    )
