from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.alert import AlertPreferenceCreate, AlertPreferenceRead, NotificationRead
from app.services.alert_service import (
    list_alert_preferences,
    list_notifications,
    mark_notification_read,
    save_alert_preference,
)


router = APIRouter()


@router.get("/preferences", response_model=list[AlertPreferenceRead])
def read_alert_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AlertPreferenceRead]:
    return list_alert_preferences(db, current_user.id)


@router.post("/preferences", response_model=AlertPreferenceRead, status_code=status.HTTP_201_CREATED)
def create_or_update_alert_preference(
    payload: AlertPreferenceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AlertPreferenceRead:
    return save_alert_preference(db, current_user.id, payload)


@router.get("/notifications", response_model=list[NotificationRead])
def read_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[NotificationRead]:
    return list_notifications(db, current_user)


@router.post("/notifications/{notification_id}/read", response_model=NotificationRead)
def read_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationRead:
    notification = mark_notification_read(db, current_user.id, notification_id)
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    return notification
