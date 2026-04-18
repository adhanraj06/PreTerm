from pydantic import BaseModel, Field, HttpUrl

from app.schemas.headline import HeadlineMapCandidate


class SentimentResult(BaseModel):
    source: str
    source_label: str = ""
    title_text: str
    compound_score: float
    sentiment_label: str
    matched_market: HeadlineMapCandidate | None = None
    extraction_note: str | None = None


class AnalyzeTextRequest(BaseModel):
    text: str = Field(min_length=8, max_length=8000)
    source: str = Field(default="manual_entry", max_length=80)
    title: str | None = Field(default=None, max_length=240)


class AnalyzeRedditHotRequest(BaseModel):
    subreddit: str = Field(default="worldnews", min_length=2, max_length=32)
    limit: int = Field(default=8, ge=2, le=15)


class AnalyzeUrlRequest(BaseModel):
    url: HttpUrl


class AnalyzeBatchRequest(BaseModel):
    items: list[AnalyzeTextRequest] = Field(min_length=1, max_length=10)


class AnalyzeBatchResponse(BaseModel):
    results: list[SentimentResult]
