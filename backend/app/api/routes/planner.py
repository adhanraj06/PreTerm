from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.planner import PlannedEventCreate, PlannedEventRead
from app.services.planner_service import (
    create_planned_event,
    delete_planned_event,
    list_planned_events,
    serialize_planned_event,
)


router = APIRouter()


@router.get("/events", response_model=list[PlannedEventRead])
def read_planned_events(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PlannedEventRead]:
    events = list_planned_events(db, current_user.id)
    return [PlannedEventRead.model_validate(serialize_planned_event(db, event)) for event in events]


@router.post("/events", response_model=PlannedEventRead, status_code=status.HTTP_201_CREATED)
def create_planned_event_route(
    payload: PlannedEventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PlannedEventRead:
    event = create_planned_event(db, current_user.id, payload)
    return PlannedEventRead.model_validate(serialize_planned_event(db, event))


@router.delete("/events/{planned_event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_planned_event_route(
    planned_event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    deleted = delete_planned_event(db, current_user.id, planned_event_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Planned event not found.")
