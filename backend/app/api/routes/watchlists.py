from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.watchlist import WatchlistCreate, WatchlistItemCreate, WatchlistRead
from app.services.watchlist_service import (
    add_watchlist_item,
    create_watchlist,
    delete_watchlist,
    delete_watchlist_item,
    list_watchlists,
)


router = APIRouter()


@router.get("", response_model=list[WatchlistRead])
def read_watchlists(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[WatchlistRead]:
    return list_watchlists(db, current_user.id)


@router.post("", response_model=WatchlistRead, status_code=status.HTTP_201_CREATED)
def create_watchlist_route(
    payload: WatchlistCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WatchlistRead:
    return create_watchlist(db, current_user.id, payload)


@router.delete("/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_watchlist_route(
    watchlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    deleted = delete_watchlist(db, current_user.id, watchlist_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist not found.")


@router.post("/{watchlist_id}/items", response_model=WatchlistRead, status_code=status.HTTP_201_CREATED)
def create_watchlist_item_route(
    watchlist_id: int,
    payload: WatchlistItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WatchlistRead:
    watchlist = add_watchlist_item(db, current_user.id, watchlist_id, payload)
    if watchlist is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist not found.")
    return watchlist


@router.delete("/{watchlist_id}/items/{item_id}", response_model=WatchlistRead)
def delete_watchlist_item_route(
    watchlist_id: int,
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WatchlistRead:
    watchlist = delete_watchlist_item(db, current_user.id, watchlist_id, item_id)
    if watchlist is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist item not found.",
        )
    return watchlist
