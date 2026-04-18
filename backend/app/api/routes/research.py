from fastapi import APIRouter, HTTPException, Query, status

from app.core.config import settings
from app.integrations.yfinance_client import YFinanceClient
from app.schemas.finance import AssetContextRead
from app.schemas.macro import MacroSeriesRead
from app.schemas.news import NewsFeedResponse, NewsItem
from app.schemas.research import MacroCatalogItem, ResearchQuoteResponse
from app.services.macro_service import get_research_macro_series, list_research_macro_catalog
from app.services.news_feed_service import fetch_equity_news_bundle

router = APIRouter()


@router.get("/macro/catalog", response_model=list[MacroCatalogItem])
def read_macro_catalog() -> list[MacroCatalogItem]:
    return [MacroCatalogItem(**row) for row in list_research_macro_catalog()]


@router.get("/macro/{series_key}", response_model=MacroSeriesRead)
def read_macro_series(series_key: str) -> MacroSeriesRead:
    series = get_research_macro_series(series_key)
    if series is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unknown series key or macro data unavailable (FRED key / fred.csv).",
        )
    return series


@router.get("/equity-news", response_model=NewsFeedResponse)
def read_equity_news(
    ticker: str = Query(..., min_length=1, max_length=12),
    reddit_subreddit: str = Query("stocks", min_length=2, max_length=32),
) -> NewsFeedResponse:
    rows = fetch_equity_news_bundle(ticker, reddit_subreddit=reddit_subreddit.strip())
    return NewsFeedResponse(items=[NewsItem.model_validate(r) for r in rows])


@router.get("/quote", response_model=ResearchQuoteResponse)
def read_equity_quote(ticker: str = Query(..., min_length=1, max_length=16)) -> ResearchQuoteResponse:
    if not settings.enable_yfinance:
        return ResearchQuoteResponse(available=False, reason="Yahoo Finance is disabled.", asset=None)
    raw = YFinanceClient().get_asset_context(ticker.strip().upper())
    if raw is None:
        return ResearchQuoteResponse(
            available=False,
            reason="Could not load that symbol from Yahoo Finance.",
            asset=None,
        )
    return ResearchQuoteResponse(available=True, asset=AssetContextRead.model_validate(raw))
