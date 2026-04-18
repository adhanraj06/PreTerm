import json

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.saved_view import SavedView
from app.schemas.saved_view import SavedViewCreate


def _saved_view_query(user_id: int) -> Select[tuple[SavedView]]:
    return (
        select(SavedView)
        .where(SavedView.user_id == user_id)
        .order_by(SavedView.updated_at.desc())
    )


def list_saved_views(db: Session, user_id: int) -> list[SavedView]:
    return list(db.scalars(_saved_view_query(user_id)).all())


def create_saved_view(db: Session, user_id: int, payload: SavedViewCreate) -> SavedView:
    saved_view = SavedView(
        user_id=user_id,
        name=payload.name.strip(),
        layout_json=json.dumps(payload.layout_json) if payload.layout_json is not None else None,
        filters_json=json.dumps(payload.filters_json) if payload.filters_json is not None else None,
    )
    db.add(saved_view)
    db.commit()
    return db.scalar(select(SavedView).where(SavedView.id == saved_view.id)) or saved_view


def delete_saved_view(db: Session, user_id: int, saved_view_id: int) -> bool:
    saved_view = db.scalar(
        select(SavedView).where(SavedView.user_id == user_id, SavedView.id == saved_view_id)
    )
    if saved_view is None:
        return False
    db.delete(saved_view)
    db.commit()
    return True
