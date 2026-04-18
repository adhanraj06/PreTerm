from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.saved_view import SavedViewCreate, SavedViewRead
from app.services.saved_view_service import create_saved_view, delete_saved_view, list_saved_views


router = APIRouter()


@router.get("", response_model=list[SavedViewRead])
def read_saved_views(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SavedViewRead]:
    return list_saved_views(db, current_user.id)


@router.post("", response_model=SavedViewRead, status_code=status.HTTP_201_CREATED)
def create_saved_view_route(
    payload: SavedViewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SavedViewRead:
    return create_saved_view(db, current_user.id, payload)


@router.delete("/{saved_view_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_view_route(
    saved_view_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    deleted = delete_saved_view(db, current_user.id, saved_view_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved view not found.")
