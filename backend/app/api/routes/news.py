from fastapi import APIRouter, HTTPException, Query

from app.schemas.news import NewsFeedResponse, NewsItem
from app.services.news_feed_service import DEFAULT_RSS_FEEDS, fetch_reddit_hot, fetch_rss_headlines

router = APIRouter()


@router.get("/reddit", response_model=NewsFeedResponse)
def read_reddit_hot(
    subreddit: str = Query("worldnews", min_length=2, max_length=32),
    limit: int = Query(12, ge=1, le=25),
) -> NewsFeedResponse:
    rows = fetch_reddit_hot(subreddit, limit)
    return NewsFeedResponse(
        items=[
            NewsItem(
                title=str(r["title"]),
                text=str(r["text"]),
                url=str(r["url"]) if r.get("url") else None,
                source=str(r["source"]) if r.get("source") else None,
                score=int(r["score"]) if r.get("score") is not None else None,
            )
            for r in rows
        ]
    )


@router.get("/rss/{feed_key}", response_model=NewsFeedResponse)
def read_curated_rss(
    feed_key: str,
    limit: int = Query(15, ge=1, le=30),
) -> NewsFeedResponse:
    url = DEFAULT_RSS_FEEDS.get(feed_key)
    if not url:
        raise HTTPException(status_code=404, detail="Unknown feed key.")
    rows = fetch_rss_headlines(url, limit)
    return NewsFeedResponse(
        items=[
            NewsItem(
                title=str(r["title"]),
                text=str(r["text"]),
                url=str(r["url"]) if r.get("url") else None,
                source=str(r.get("source") or "RSS"),
            )
            for r in rows
        ]
    )


@router.get("/feeds", response_model=dict[str, str])
def list_feeds() -> dict[str, str]:
    return dict(DEFAULT_RSS_FEEDS)
