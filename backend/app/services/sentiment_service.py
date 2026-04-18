from __future__ import annotations
import re
from html import unescape
from urllib.parse import urlparse

import httpx
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from sqlalchemy.orm import Session

from app.schemas.headline import HeadlineMapCandidate
from app.schemas.sentiment import SentimentResult
from app.services.headline_service import map_headline_to_markets


TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
OG_TITLE_RE = re.compile(
    r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\'](.*?)["\']',
    re.IGNORECASE | re.DOTALL,
)
OG_DESC_RE = re.compile(
    r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\'](.*?)["\']',
    re.IGNORECASE | re.DOTALL,
)
META_DESC_RE = re.compile(
    r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
    re.IGNORECASE | re.DOTALL,
)
TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")

_vader_analyzer: SentimentIntensityAnalyzer | None = None


def ensure_vader_ready() -> bool:
    try:
        nltk.data.find("sentiment/vader_lexicon.zip")
        return True
    except LookupError:
        try:
            return bool(nltk.download("vader_lexicon", quiet=True))
        except Exception:
            return False


def get_vader_analyzer() -> SentimentIntensityAnalyzer | None:
    global _vader_analyzer
    if _vader_analyzer is None:
        if not ensure_vader_ready():
            return None
        try:
            _vader_analyzer = SentimentIntensityAnalyzer()
        except LookupError:
            return None
    return _vader_analyzer


def sentiment_source_label(source: str) -> str:
    key = source.lower().strip()
    canned: dict[str, str] = {
        "manual_entry": "Manual text",
        "pasted_text": "Manual text",
        "reddit_hot": "Reddit · hot posts",
        "batch_text": "Batch",
    }
    if key in canned:
        return canned[key]
    if key == "url":
        return "Article or page URL"
    if "." in source and not source.startswith("http"):
        host = source.lower().removeprefix("www.")
        return host[:56]
    return source.replace("_", " ").strip().title() or "Unknown"


def _sentiment_label(score: float) -> str:
    if score >= 0.15:
        return "bullish"
    if score <= -0.15:
        return "bearish"
    return "neutral"


def _strip_tags(value: str) -> str:
    cleaned = TAG_RE.sub(" ", value)
    return WHITESPACE_RE.sub(" ", unescape(cleaned)).strip()


def _extract_html_text(html: str) -> tuple[str | None, str | None]:
    og_title = OG_TITLE_RE.search(html)
    og_desc = OG_DESC_RE.search(html)
    meta_desc = META_DESC_RE.search(html)
    title = og_title.group(1) if og_title else None
    if not title:
        title_match = TITLE_RE.search(html)
        title = title_match.group(1) if title_match else None
    description = og_desc.group(1) if og_desc else None
    if not description and meta_desc:
        description = meta_desc.group(1)
    return (
        _strip_tags(title) if title else None,
        _strip_tags(description) if description else None,
    )


def _fetch_reddit_text(url: str) -> tuple[str | None, str | None, str | None]:
    json_url = url.rstrip("/")
    if not json_url.endswith(".json"):
        json_url = f"{json_url}.json"

    headers = {"User-Agent": "PreTermSentiment/1.0"}
    with httpx.Client(timeout=10.0, headers=headers, follow_redirects=True) as client:
        response = client.get(json_url)
        response.raise_for_status()
        payload = response.json()

    if not isinstance(payload, list) or not payload:
        return None, None, "Reddit response did not include usable thread data."

    try:
        post = payload[0]["data"]["children"][0]["data"]
    except (KeyError, IndexError, TypeError):
        return None, None, "Unable to parse Reddit thread JSON."

    title = str(post.get("title") or "").strip() or None
    selftext = str(post.get("selftext") or "").strip() or None
    combined = " ".join(part for part in [title, selftext] if part).strip() or None
    return title, combined, None if combined else "Reddit thread was empty."


def _extract_url_text(url: str) -> tuple[str | None, str | None, str | None]:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()

    if "reddit.com" in hostname or "redd.it" in hostname:
        return _fetch_reddit_text(url)

    if "x.com" in hostname or "twitter.com" in hostname:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml",
        }
        with httpx.Client(timeout=12.0, headers=headers, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            title, description = _extract_html_text(response.text)
        combined = " ".join(part for part in [title, description] if part).strip() or None
        note = None
        if not combined:
            note = (
                "X/Twitter did not return readable preview text (login wall or bot block). "
                "Paste the post text for a reliable score."
            )
        return title, combined, note

    headers = {"User-Agent": "PreTermSentiment/1.0"}
    with httpx.Client(timeout=10.0, headers=headers, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
        title, description = _extract_html_text(response.text)

    combined = " ".join(part for part in [title, description] if part).strip() or None
    if not combined:
        return None, None, "Unable to extract readable text from the URL. Paste the text instead."
    return title, combined, None


def analyze_text_sentiment(
    db: Session,
    text: str,
    *,
    source: str = "manual_entry",
    title: str | None = None,
    extraction_note: str | None = None,
) -> SentimentResult:
    analyzer = get_vader_analyzer()
    text_to_score = text.strip()
    market_map = map_headline_to_markets(db, text_to_score[:500])
    matched_market: HeadlineMapCandidate | None = market_map.top_match
    title_text = (title or text_to_score).strip()[:500]
    if analyzer is None:
        return SentimentResult(
            source=source,
            source_label=sentiment_source_label(source),
            title_text=title_text,
            compound_score=0.0,
            sentiment_label="neutral",
            matched_market=matched_market,
            extraction_note=(
                extraction_note
                or "VADER resources are unavailable on this machine. Sentiment scoring is temporarily disabled."
            ),
        )

    compound = round(analyzer.polarity_scores(text_to_score)["compound"], 4)

    return SentimentResult(
        source=source,
        source_label=sentiment_source_label(source),
        title_text=title_text,
        compound_score=compound,
        sentiment_label=_sentiment_label(compound),
        matched_market=matched_market,
        extraction_note=extraction_note,
    )


def analyze_url_sentiment(db: Session, url: str) -> SentimentResult:
    try:
        title, extracted_text, extraction_note = _extract_url_text(url)
    except httpx.HTTPError:
        return SentimentResult(
            source="url",
            source_label=sentiment_source_label("url"),
            title_text=url,
            compound_score=0.0,
            sentiment_label="neutral",
            matched_market=None,
            extraction_note="URL extraction failed. Paste the article or post text instead.",
        )

    if not extracted_text:
        return SentimentResult(
            source="url",
            source_label=sentiment_source_label("url"),
            title_text=title or url,
            compound_score=0.0,
            sentiment_label="neutral",
            matched_market=None,
            extraction_note=extraction_note or "URL extraction failed. Paste the text instead.",
        )

    parsed = urlparse(url)
    source_key = parsed.hostname or "url"
    return analyze_text_sentiment(
        db,
        extracted_text,
        source=source_key,
        title=title or url,
        extraction_note=extraction_note,
    )


def analyze_reddit_hot_sentiment(
    db: Session,
    *,
    subreddit: str,
    limit: int = 8,
) -> SentimentResult:
    from app.services.news_feed_service import fetch_reddit_hot

    cap = max(2, min(int(limit), 15))
    sub = subreddit.strip().removeprefix("r/").lower()
    title_bar = f"r/{sub} · hot threads"
    try:
        posts = fetch_reddit_hot(subreddit, cap)
    except Exception as exc:
        return SentimentResult(
            source="reddit_hot",
            source_label=sentiment_source_label("reddit_hot"),
            title_text=title_bar,
            compound_score=0.0,
            sentiment_label="neutral",
            matched_market=None,
            extraction_note=(
                f"Could not load Reddit hot JSON ({exc.__class__.__name__}). "
                "Try old.reddit-style access from another network if blocks persist."
            ),
        )
    if not posts:
        return SentimentResult(
            source="reddit_hot",
            source_label=sentiment_source_label("reddit_hot"),
            title_text=title_bar,
            compound_score=0.0,
            sentiment_label="neutral",
            matched_market=None,
            extraction_note="No posts returned. Check the subreddit name or try again later.",
        )
    chunks: list[str] = []
    for post in posts[:10]:
        chunks.append(str(post["title"]))
        body = str(post.get("text") or "")
        if body and body != str(post["title"]) and len(body) > 40:
            chunks.append(body[:900])
    combined = "\n\n".join(chunks)[:8000]
    note = f"Blended from {len(posts)} hot posts on r/{sub} (titles and self-text where present)."
    return analyze_text_sentiment(
        db,
        combined,
        source="reddit_hot",
        title=title_bar,
        extraction_note=note,
    )


def analyze_batch_sentiment(
    db: Session,
    items: list[dict[str, str | None]],
) -> list[SentimentResult]:
    results: list[SentimentResult] = []
    for item in items:
        results.append(
            analyze_text_sentiment(
                db,
                str(item.get("text") or ""),
                source=str(item.get("source") or "batch_text"),
                title=str(item.get("title")) if item.get("title") is not None else None,
            )
        )
    return results
