from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from app.models.market import Market
from app.models.watchlist import Watchlist, WatchlistItem
from app.schemas.watchlist import WatchlistCreate, WatchlistItemCreate


def _watchlist_query(user_id: int) -> Select[tuple[Watchlist]]:
    return (
        select(Watchlist)
        .where(Watchlist.user_id == user_id)
        .options(selectinload(Watchlist.items).selectinload(WatchlistItem.market))
        .order_by(Watchlist.updated_at.desc())
    )


def _get_watchlist(db: Session, user_id: int, watchlist_id: int) -> Watchlist | None:
    return db.scalar(_watchlist_query(user_id).where(Watchlist.id == watchlist_id))


def list_watchlists(db: Session, user_id: int) -> list[Watchlist]:
    return list(db.scalars(_watchlist_query(user_id)).all())


def create_watchlist(db: Session, user_id: int, payload: WatchlistCreate) -> Watchlist:
    watchlist = Watchlist(user_id=user_id, name=payload.name.strip())
    db.add(watchlist)
    db.commit()
    return _get_watchlist(db, user_id, watchlist.id) or watchlist


def delete_watchlist(db: Session, user_id: int, watchlist_id: int) -> bool:
    watchlist = _get_watchlist(db, user_id, watchlist_id)
    if watchlist is None:
        return False
    db.delete(watchlist)
    db.commit()
    return True


def add_watchlist_item(
    db: Session,
    user_id: int,
    watchlist_id: int,
    payload: WatchlistItemCreate,
) -> Watchlist | None:
    watchlist = _get_watchlist(db, user_id, watchlist_id)
    if watchlist is None:
        return None

    market = db.get(Market, payload.market_id)
    if market is None:
        return None

    duplicate = next((item for item in watchlist.items if item.market_id == payload.market_id), None)
    if duplicate is None:
        db.add(
            WatchlistItem(
                watchlist_id=watchlist.id,
                market_id=payload.market_id,
                position=payload.position,
                notes=payload.notes,
            )
        )
        db.commit()
    return _get_watchlist(db, user_id, watchlist_id)


def delete_watchlist_item(
    db: Session,
    user_id: int,
    watchlist_id: int,
    item_id: int,
) -> Watchlist | None:
    watchlist = _get_watchlist(db, user_id, watchlist_id)
    if watchlist is None:
        return None

    item = next((entry for entry in watchlist.items if entry.id == item_id), None)
    if item is None:
        return None

    db.delete(item)
    db.commit()
    return _get_watchlist(db, user_id, watchlist_id)
