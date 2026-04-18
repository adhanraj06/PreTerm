import json

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.alert import AlertPreference
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User, UserPreference, UserProfile
from app.schemas.auth import AuthResponse, AuthToken, LoginRequest, RegisterRequest


def _get_user_with_relations(db: Session, email: str) -> User | None:
    statement = (
        select(User)
        .options(selectinload(User.profile), selectinload(User.preference))
        .where(User.email == email.lower())
    )
    return db.scalar(statement)


def _build_auth_response(user: User) -> AuthResponse:
    token = create_access_token(subject=str(user.id))
    return AuthResponse(
        token=AuthToken(access_token=token),
        user=user,
    )


def register_user(db: Session, payload: RegisterRequest) -> AuthResponse:
    email = payload.email.lower()
    existing_user = _get_user_with_relations(db, email=email)
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with that email already exists.",
        )

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name.strip(),
    )
    db.add(user)
    db.flush()

    db.add(UserProfile(user_id=user.id))
    db.add(
        UserPreference(
            user_id=user.id,
            preferred_categories=json.dumps([]),
            preferred_desk_mode=None,
            alert_move_threshold=None,
            alert_headline_matches=True,
        )
    )
    db.add_all(
        [
            AlertPreference(user_id=user.id, rule_type="move_threshold", threshold_value=5, enabled=True),
            AlertPreference(user_id=user.id, rule_type="mapped_headline", threshold_value=None, enabled=True),
            AlertPreference(user_id=user.id, rule_type="threshold_range", threshold_value=60, enabled=True),
        ]
    )
    db.commit()
    db.refresh(user)

    created_user = _get_user_with_relations(db, email=email)
    if created_user is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User registration failed.",
        )

    return _build_auth_response(created_user)


def login_user(db: Session, payload: LoginRequest) -> AuthResponse:
    user = _get_user_with_relations(db, email=payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    return _build_auth_response(user)
