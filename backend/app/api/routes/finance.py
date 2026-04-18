from fastapi import APIRouter, Query

from app.core.config import settings
from app.integrations.edgar_client import EdgarClient
from app.schemas.finance import EdgarBrowseResponse, EdgarFilingRead

router = APIRouter()


@router.get("/edgar/filings", response_model=EdgarBrowseResponse)
def browse_edgar_filings(
    ticker: str = Query(..., min_length=1, max_length=12),
    forms: str = Query("10-K,10-Q,8-K", max_length=200),
    limit: int = Query(12, ge=1, le=40),
) -> EdgarBrowseResponse:
    if not settings.enable_edgar:
        return EdgarBrowseResponse(
            available=False,
            reason="EDGAR integration is disabled.",
            ticker=ticker.strip().upper(),
            company_name="",
            cik="",
            filings=[],
        )

    form_list = [part.strip() for part in forms.split(",") if part.strip()]
    payload = EdgarClient().fetch_filings(ticker, forms=form_list, limit=limit)
    if payload is None:
        return EdgarBrowseResponse(
            available=False,
            reason=(
                "Could not load SEC filings (ticker not found, EDGAR disabled, or blocked request). "
                "Set EDGAR_IDENTITY / SEC_USER_AGENT to a real contact string per SEC fair access."
            ),
            ticker=ticker.strip().upper(),
            company_name="",
            cik="",
            filings=[],
        )

    filings_raw = payload.get("latest_filings", [])
    filings = [EdgarFilingRead.model_validate(row) for row in filings_raw]

    return EdgarBrowseResponse(
        available=True,
        ticker=ticker.strip().upper(),
        company_name=str(payload.get("company_name") or ""),
        cik=str(payload.get("cik") or ""),
        filings=filings,
    )
