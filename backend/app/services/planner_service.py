from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.market import Market
from app.models.planner import PlannedEvent
from app.schemas.planner import PlannedEventCreate, PlannedEventMarketSuggestion
from app.schemas.watchlist import WatchlistMarketSummary
from app.services.headline_service import _market_text_tokens, _tokenize
from app.services.market_service import list_markets


CONCERN_HINTS: dict[str, set[str]] = {
    "weather": {"cpi", "inflation", "yield", "fed", "recession"},
    "travel": {"recession", "yield", "shutdown", "inflation"},
    "game_day": {"celtics", "chiefs", "playoffs", "title", "inflation"},
    "policy": {"shutdown", "stablecoin", "house", "senate", "approval"},
    "business": {"fed", "yield", "recession", "nvidia", "amazon", "tesla", "spx"},
    "crypto": {"bitcoin", "ethereum", "solana", "stablecoin", "fed"},
}


@dataclass
class RankedSuggestion:
    market: Market
    score: float
    rationale: str


def _planned_event_query(user_id: int) -> Select[tuple[PlannedEvent]]:
    return select(PlannedEvent).where(PlannedEvent.user_id == user_id).order_by(PlannedEvent.date.asc())


def _build_context_tokens(event: PlannedEvent | PlannedEventCreate) -> set[str]:
    parts = [event.title, event.concern_type]
    if event.location:
        parts.append(event.location)
    if event.notes:
        parts.append(event.notes)
    tokens = _tokenize(" ".join(parts))
    tokens.update(CONCERN_HINTS.get(event.concern_type.lower(), set()))
    return tokens


def _build_rationale(matched_tokens: Iterable[str], concern_type: str) -> str:
    matched = list(sorted(set(matched_tokens)))[:4]
    if matched:
        return f"Matched on {', '.join(matched)} for the {concern_type} planning concern."
    return f"Suggested as a broad monitoring contract for the {concern_type} planning concern."


def suggest_markets_for_event(
    event: PlannedEvent | PlannedEventCreate,
    markets: list[Market],
) -> list[PlannedEventMarketSuggestion]:
    context_tokens = _build_context_tokens(event)
    ranked: list[RankedSuggestion] = []

    for market in markets:
        market_tokens = _market_text_tokens(market)
        matched_tokens = context_tokens & market_tokens
        score = float(len(matched_tokens))
        if market.category == "macro" and event.concern_type.lower() in {"weather", "travel", "business"}:
            score += 0.5
        if market.category in {"sports", "politics"} and event.concern_type.lower() in {"game_day", "policy"}:
            score += 0.75
        if market.category in {"equities", "crypto"} and event.concern_type.lower() in {"business", "crypto"}:
            score += 0.75
        if score <= 0:
            continue

        ranked.append(
            RankedSuggestion(
                market=market,
                score=score,
                rationale=_build_rationale(matched_tokens, event.concern_type),
            )
        )

    ranked.sort(key=lambda item: (item.score, item.market.last_price), reverse=True)
    return [
        PlannedEventMarketSuggestion(
            market=WatchlistMarketSummary.model_validate(item.market),
            relevance_score=round(min(0.98, item.score / 6.0), 2),
            rationale=item.rationale,
        )
        for item in ranked[:4]
    ]


def list_planned_events(db: Session, user_id: int) -> list[PlannedEvent]:
    return list(db.scalars(_planned_event_query(user_id)).all())


def create_planned_event(db: Session, user_id: int, payload: PlannedEventCreate) -> PlannedEvent:
    planned_event = PlannedEvent(
        user_id=user_id,
        title=payload.title.strip(),
        date=payload.date,
        location=payload.location.strip() if payload.location else None,
        concern_type=payload.concern_type.strip(),
        notes=payload.notes.strip() if payload.notes else None,
    )
    db.add(planned_event)
    db.commit()
    db.refresh(planned_event)
    return planned_event


def delete_planned_event(db: Session, user_id: int, planned_event_id: int) -> bool:
    planned_event = db.scalar(_planned_event_query(user_id).where(PlannedEvent.id == planned_event_id))
    if planned_event is None:
        return False
    db.delete(planned_event)
    db.commit()
    return True


def serialize_planned_event(db: Session, planned_event: PlannedEvent) -> dict[str, object]:
    markets = list_markets(db)
    return {
        "id": planned_event.id,
        "title": planned_event.title,
        "date": planned_event.date,
        "location": planned_event.location,
        "concern_type": planned_event.concern_type,
        "notes": planned_event.notes,
        "created_at": planned_event.created_at,
        "updated_at": planned_event.updated_at,
        "suggestions": suggest_markets_for_event(planned_event, markets),
    }
