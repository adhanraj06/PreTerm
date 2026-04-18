from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.sentiment import (
    AnalyzeBatchRequest,
    AnalyzeBatchResponse,
    AnalyzeRedditHotRequest,
    AnalyzeTextRequest,
    AnalyzeUrlRequest,
    SentimentResult,
)
from app.services.sentiment_service import (
    analyze_batch_sentiment,
    analyze_reddit_hot_sentiment,
    analyze_text_sentiment,
    analyze_url_sentiment,
)


router = APIRouter()


@router.post("/analyze-text", response_model=SentimentResult)
def analyze_text(payload: AnalyzeTextRequest, db: Session = Depends(get_db)) -> SentimentResult:
    return analyze_text_sentiment(
        db,
        payload.text,
        source=payload.source,
        title=payload.title,
    )


@router.post("/analyze-url", response_model=SentimentResult)
def analyze_url(payload: AnalyzeUrlRequest, db: Session = Depends(get_db)) -> SentimentResult:
    return analyze_url_sentiment(db, str(payload.url))


@router.post("/analyze-reddit-hot", response_model=SentimentResult)
def analyze_reddit_hot(payload: AnalyzeRedditHotRequest, db: Session = Depends(get_db)) -> SentimentResult:
    return analyze_reddit_hot_sentiment(
        db,
        subreddit=payload.subreddit,
        limit=payload.limit,
    )


@router.post("/analyze-batch", response_model=AnalyzeBatchResponse)
def analyze_batch(
    payload: AnalyzeBatchRequest,
    db: Session = Depends(get_db),
) -> AnalyzeBatchResponse:
    return AnalyzeBatchResponse(
        results=analyze_batch_sentiment(db, [item.model_dump() for item in payload.items])
    )
