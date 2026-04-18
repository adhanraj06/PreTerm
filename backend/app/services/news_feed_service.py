"""Fetch public headlines from Reddit and RSS (no API keys)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from urllib.parse import quote

import httpx

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 PreTerm/1.0"
)

DEFAULT_RSS_FEEDS: dict[str, str] = {
    "bbc_world": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "npr_news": "https://feeds.npr.org/1001/rss.xml",
}


def _client() -> httpx.Client:
    return httpx.Client(
        timeout=20.0,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json, application/rss+xml, text/xml, */*"},
        follow_redirects=True,
    )


def fetch_reddit_hot(subreddit: str, limit: int = 12) -> list[dict[str, str | int | None]]:
    sub = subreddit.strip().removeprefix("r/").lower()
    if not sub or not all(part.isalnum() or part == "_" for part in sub.split("_")) or len(sub) > 32:
        return []

    limit = max(1, min(limit, 25))
    urls = (
        f"https://old.reddit.com/r/{sub}/hot.json?limit={limit}&raw_json=1",
        f"https://www.reddit.com/r/{sub}/hot.json?limit={limit}&raw_json=1",
    )

    payload: dict | None = None
    last_err: Exception | None = None
    with _client() as client:
        for url in urls:
            try:
                response = client.get(url)
                response.raise_for_status()
                payload = response.json()
                break
            except Exception as exc:
                last_err = exc
                continue
    if payload is None and last_err is not None:
        raise last_err
    if payload is None:
        return []

    out: list[dict[str, str | int | None]] = []
    children = (payload.get("data") or {}).get("children") or []
    for child in children:
        data = (child or {}).get("data") or {}
        if data.get("stickied"):
            continue
        title = str(data.get("title") or "").strip()
        if not title:
            continue
        selftext = str(data.get("selftext") or "").strip()
        permalink = data.get("permalink")
        link = f"https://www.reddit.com{permalink}" if permalink else None
        score = data.get("ups")
        score_int: int | None
        if isinstance(score, (int, float)):
            score_int = int(score)
        else:
            score_int = None
        out.append(
            {
                "title": title,
                "text": selftext or title,
                "url": link,
                "score": score_int,
                "source": f"r/{sub}",
            }
        )
    return out


def fetch_rss_headlines(feed_url: str, limit: int = 15) -> list[dict[str, str | None]]:
    limit = max(1, min(limit, 30))

    with _client() as client:
        response = client.get(feed_url)
        response.raise_for_status()
        raw = response.content

    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return []

    items: list[dict[str, str | None]] = []

    for item in root.findall(".//item"):
        title_el = item.find("title")
        link_el = item.find("link")
        desc_el = item.find("description")
        title = (title_el.text or "").strip() if title_el is not None and title_el.text else ""
        link = (link_el.text or "").strip() if link_el is not None and link_el.text else None
        desc = (desc_el.text or "").strip() if desc_el is not None and desc_el.text else None
        if not title:
            continue
        text = f"{title}\n{desc}" if desc else title
        items.append({"title": title, "text": text, "url": link, "source": "RSS"})
        if len(items) >= limit:
            break

    if not items:
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall(".//atom:entry", ns):
            title_el = entry.find("atom:title", ns)
            link_el = entry.find("atom:link", ns)
            summary_el = entry.find("atom:summary", ns)
            title = (title_el.text or "").strip() if title_el is not None and title_el.text else ""
            href = link_el.get("href") if link_el is not None else None
            summary = (summary_el.text or "").strip() if summary_el is not None and summary_el.text else None
            if not title:
                continue
            text = f"{title}\n{summary}" if summary else title
            items.append({"title": title, "text": text, "url": href, "source": "Atom"})
            if len(items) >= limit:
                break

    return items


def fetch_equity_news_bundle(
    ticker: str,
    *,
    reddit_subreddit: str = "stocks",
    rss_limit: int = 22,
    reddit_limit: int = 12,
) -> list[dict[str, str | int | None]]:
    """Ticker-focused RSS (Google News) plus Reddit hot — always via backend to avoid browser CORS."""
    t = ticker.strip().upper()
    merged: list[dict[str, str | int | None]] = []

    gq = quote(f"{t} stock OR {t} earnings")
    gurl = f"https://news.google.com/rss/search?q={gq}&hl=en-US&gl=US&ceid=US:en"
    for row in fetch_rss_headlines(gurl, rss_limit):
        item = dict(row)
        item["source"] = "Google News"
        merged.append(item)

    sub = reddit_subreddit.strip().removeprefix("r/").lower()
    try:
        reddit_rows = fetch_reddit_hot(sub, reddit_limit)
    except Exception:
        reddit_rows = []
    for row in reddit_rows:
        merged.append(dict(row))

    seen: set[str] = set()
    deduped: list[dict[str, str | int | None]] = []
    for row in merged:
        title = (row.get("title") or "").strip().lower()
        if not title or title in seen:
            continue
        seen.add(title)
        deduped.append(row)
    return deduped[:55]
