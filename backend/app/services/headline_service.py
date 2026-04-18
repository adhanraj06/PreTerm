import json
import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.market import Market
from app.schemas.headline import HeadlineMapCandidate, HeadlineMapResponse
from app.services.market_service import list_markets


TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9$]+")

POSITIVE_HINTS = {
    "cooler",
    "beat",
    "surge",
    "rally",
    "cut",
    "cuts",
    "drop",
    "fall",
    "strong",
    "breakout",
    "positive",
    "expand",
    "wins",
    "lead",
    "eases",
}

NEGATIVE_HINTS = {
    "sticky",
    "miss",
    "slump",
    "selloff",
    "shock",
    "shutdown",
    "weaker",
    "recession",
    "stress",
    "delay",
    "bearish",
    "tighten",
    "tightening",
    "hot",
}

MARKET_KEYWORDS: dict[str, set[str]] = {
    "fed-two-cuts-by-september-2026": {"fed", "rate", "rates", "cut", "cuts", "fomc", "inflation", "cpi", "pce", "payrolls"},
    "us-recession-by-q4-2026": {"recession", "growth", "consumer", "spending", "claims", "ism", "economy"},
    "core-cpi-below-3-by-august-2026": {"cpi", "inflation", "core", "shelter", "prices", "disinflation"},
    "democrats-win-house-2026": {"house", "generic", "ballot", "district", "suburban", "midterm", "democrats"},
    "republicans-control-senate-2026": {"senate", "battleground", "republicans", "recruitment", "polling"},
    "presidential-approval-over-50-by-july-2026": {"approval", "poll", "president", "favorability"},
    "bitcoin-new-all-time-high-by-december-2026": {"bitcoin", "btc", "crypto", "etf", "flows", "digital", "ath"},
    "spot-eth-etf-flows-positive-q3-2026": {"eth", "ethereum", "etf", "flows", "crypto"},
    "sol-above-200-before-october-2026": {"sol", "solana", "alts", "crypto", "token"},
    "sp500-close-above-6000-by-august-2026": {"s&p", "spx", "index", "equities", "stocks", "earnings"},
    "nvidia-next-quarter-revenue-beat": {"nvidia", "nvda", "ai", "chips", "revenue", "earnings", "hyperscaler"},
    "tesla-next-quarter-deliveries-above-consensus": {"tesla", "deliveries", "autos", "ev"},
    "amazon-operating-margin-expand-next-quarter": {"amazon", "margin", "aws", "cloud", "retail"},
    "celtics-win-2026-nba-title": {"celtics", "nba", "playoffs", "title", "finals"},
    "chiefs-make-2026-nfl-playoffs": {"chiefs", "nfl", "playoffs", "mahomes"},
    "us10y-yield-below-4-by-july-2026": {"10-year", "10y", "treasury", "yield", "rates", "bond"},
    "government-shutdown-before-october-2026": {"shutdown", "budget", "congress", "appropriations"},
    "major-stablecoin-legislation-by-december-2026": {"stablecoin", "legislation", "congress", "crypto", "bill"},
}


@dataclass
class MatchScore:
    market: Market
    raw_score: float
    confidence: float
    directional_impact: str
    explanation: str
    why_it_matters: str


def _tokenize(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_PATTERN.findall(text)}


def _market_text_tokens(market: Market) -> set[str]:
    tokens = _tokenize(market.title)
    tokens.update(_tokenize(market.category))
    if market.description:
        tokens.update(_tokenize(market.description))
    if market.metadata_json:
        try:
            metadata = json.loads(market.metadata_json)
            tokens.update(_tokenize(json.dumps(metadata)))
        except json.JSONDecodeError:
            pass
    if market.brief:
        tokens.update(_tokenize(market.brief.summary))
        tokens.update(_tokenize(market.brief.why_this_matters_now))
        tokens.update(_tokenize(market.brief.what_changed))
    tokens.update(MARKET_KEYWORDS.get(market.slug, set()))
    return tokens


def _directional_impact(tokens: set[str]) -> str:
    positive_hits = len(tokens & POSITIVE_HINTS)
    negative_hits = len(tokens & NEGATIVE_HINTS)

    if positive_hits > negative_hits:
        return "bullish"
    if negative_hits > positive_hits:
        return "bearish"
    return "mixed"


def _build_match(market: Market, headline_text: str) -> MatchScore:
    headline_tokens = _tokenize(headline_text)
    market_tokens = _market_text_tokens(market)
    matched_tokens = headline_tokens & market_tokens

    raw_score = float(len(matched_tokens))
    if market.slug in MARKET_KEYWORDS:
        raw_score += 0.5 * len(headline_tokens & MARKET_KEYWORDS[market.slug])

    confidence = min(0.98, max(0.05, raw_score / max(6, len(headline_tokens) + 1)))
    explanation = (
        f"Matched on {', '.join(sorted(matched_tokens)[:5]) or 'broad context'} "
        f"using market title, brief, and deterministic keyword tags."
    )
    why_it_matters = (
        market.brief.why_this_matters_now
        if market.brief
        else market.description or "This contract is the closest mapped market."
    )

    return MatchScore(
        market=market,
        raw_score=raw_score,
        confidence=round(confidence, 2),
        directional_impact=_directional_impact(headline_tokens),
        explanation=explanation,
        why_it_matters=why_it_matters,
    )


def map_headline_to_markets(db: Session, headline_text: str) -> HeadlineMapResponse:
    """Deterministic headline mapper. A model-assisted Gemini layer can replace this later."""
    markets = list_markets(db)
    ranked = sorted(
        (_build_match(market, headline_text) for market in markets),
        key=lambda item: (item.raw_score, item.confidence, item.market.last_price),
        reverse=True,
    )

    candidates = [
        HeadlineMapCandidate(
            market_id=item.market.id,
            title=item.market.title,
            category=item.market.category,
            match_strength=item.confidence,
            directional_impact=item.directional_impact,
            explanation=item.explanation,
            why_it_matters=item.why_it_matters,
        )
        for item in ranked[:3]
        if item.raw_score > 0
    ]

    return HeadlineMapResponse(
        top_match=candidates[0] if candidates else None,
        candidates=candidates,
    )
