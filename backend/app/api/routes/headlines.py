from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.headline import HeadlineMapRequest, HeadlineMapResponse
from app.services.headline_service import map_headline_to_markets


router = APIRouter()


@router.post("/headline-map", response_model=HeadlineMapResponse)
def headline_map(payload: HeadlineMapRequest, db: Session = Depends(get_db)) -> HeadlineMapResponse:
    return map_headline_to_markets(db, payload.headline_text)
