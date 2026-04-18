import json

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.alert import AlertPreference, Notification
from app.models.market import Market
from app.models.user import User
from app.models.watchlist import Watchlist, WatchlistItem
from app.schemas.alert import AlertPreferenceCreate


def list_alert_preferences(db: Session, user_id: int) -> list[AlertPreference]:
    statement = (
        select(AlertPreference)
        .where(AlertPreference.user_id == user_id)
        .order_by(AlertPreference.updated_at.desc())
    )
    return list(db.scalars(statement).all())


def save_alert_preference(
    db: Session, user_id: int, payload: AlertPreferenceCreate
) -> AlertPreference:
    statement = select(AlertPreference).where(
        AlertPreference.user_id == user_id,
        AlertPreference.rule_type == payload.rule_type,
        AlertPreference.market_id == payload.market_id,
    )
    existing = db.scalar(statement)
    if existing is not None:
        existing.threshold_value = payload.threshold_value
        existing.enabled = payload.enabled
        db.commit()
        db.refresh(existing)
        return existing

    preference = AlertPreference(
        user_id=user_id,
        market_id=payload.market_id,
        rule_type=payload.rule_type,
        threshold_value=payload.threshold_value,
        enabled=payload.enabled,
    )
    db.add(preference)
    db.commit()
    db.refresh(preference)
    return preference


def _watched_markets(db: Session, user_id: int) -> list[Market]:
    statement = (
        select(Watchlist)
        .where(Watchlist.user_id == user_id)
        .options(selectinload(Watchlist.items).selectinload(WatchlistItem.market))
    )
    watchlists = list(db.scalars(statement).all())
    markets: dict[int, Market] = {}
    for watchlist in watchlists:
        for item in watchlist.items:
            if item.market is not None:
                markets[item.market.id] = item.market
    return list(markets.values())


def _notification_exists(db: Session, user_id: int, kind: str, market_id: int | None, title: str) -> bool:
    statement = select(Notification).where(
        Notification.user_id == user_id,
        Notification.kind == kind,
        Notification.market_id == market_id,
        Notification.title == title,
    )
    return db.scalar(statement) is not None


def _create_notification(
    db: Session,
    user_id: int,
    kind: str,
    title: str,
    message: str,
    market_id: int | None = None,
    alert_preference_id: int | None = None,
    metadata: dict[str, object] | None = None,
) -> None:
    if _notification_exists(db, user_id, kind, market_id, title):
        return

    db.add(
        Notification(
            user_id=user_id,
            kind=kind,
            title=title,
            message=message,
            market_id=market_id,
            alert_preference_id=alert_preference_id,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
    )


def _ensure_notifications(db: Session, user: User) -> None:
    watched_markets = _watched_markets(db, user.id)
    preferences = list_alert_preferences(db, user.id)
    pref_by_rule = {pref.rule_type: pref for pref in preferences if pref.enabled and pref.market_id is None}

    move_pref = pref_by_rule.get("move_threshold")
    headline_pref = pref_by_rule.get("mapped_headline")
    threshold_pref = pref_by_rule.get("threshold_range")

    for market in watched_markets:
        move_points = abs(market.probability_change * 100)
        if move_pref and move_pref.threshold_value is not None and move_points >= move_pref.threshold_value:
            _create_notification(
                db,
                user.id,
                kind="move_threshold",
                title=f"{market.title} moved {move_points:.0f} pts",
                message=f"{market.title} exceeded your move alert threshold with a {move_points:.0f}-point shift.",
                market_id=market.id,
                alert_preference_id=move_pref.id,
                metadata={"watchlist_related": True},
            )

        if headline_pref and market.brief and market.brief.recent_headlines_json:
            headlines = json.loads(market.brief.recent_headlines_json)
            if headlines:
                headline = headlines[0]
                _create_notification(
                    db,
                    user.id,
                    kind="mapped_headline",
                    title=f"Headline mapped to {market.title}",
                    message=f"{headline['title']} now matters for {market.title}.",
                    market_id=market.id,
                    alert_preference_id=headline_pref.id,
                    metadata={"source": headline.get("source"), "watchlist_related": True},
                )

        if threshold_pref and threshold_pref.threshold_value is not None:
            threshold = threshold_pref.threshold_value / 100
            if market.last_price >= threshold:
                _create_notification(
                    db,
                    user.id,
                    kind="threshold_range",
                    title=f"{market.title} entered your alert range",
                    message=f"{market.title} is now trading at {market.last_price * 100:.0f}%, above your configured threshold range.",
                    market_id=market.id,
                    alert_preference_id=threshold_pref.id,
                    metadata={"watchlist_related": True},
                )

    db.commit()


def list_notifications(db: Session, user: User) -> list[Notification]:
    _ensure_notifications(db, user)
    statement = (
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.is_read.asc(), Notification.created_at.desc())
    )
    return list(db.scalars(statement).all())


def mark_notification_read(db: Session, user_id: int, notification_id: int) -> Notification | None:
    statement = select(Notification).where(
        Notification.user_id == user_id,
        Notification.id == notification_id,
    )
    notification = db.scalar(statement)
    if notification is None:
        return None
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification
