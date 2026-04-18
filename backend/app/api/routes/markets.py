from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.finance import FinanceContextResponse
from app.schemas.macro import MacroContextResponse
from app.schemas.market import MarketDetail, MarketListItem
from app.services.finance_service import get_finance_context
from app.services.macro_service import get_macro_context
from app.services.market_service import get_market_by_id, list_markets


router = APIRouter()


@router.get("", response_model=list[MarketListItem])
def read_markets(db: Session = Depends(get_db)) -> list[MarketListItem]:
    return list_markets(db)


@router.get("/{market_id}", response_model=MarketDetail)
def read_market(market_id: int, db: Session = Depends(get_db)) -> MarketDetail:
    market = get_market_by_id(db, market_id)
    if market is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found.",
        )
    return market


@router.get("/{market_id}/macro-context", response_model=MacroContextResponse)
def read_market_macro_context(market_id: int, db: Session = Depends(get_db)) -> MacroContextResponse:
    context = get_macro_context(db, market_id)
    if context is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found.",
        )
    return context


@router.get("/{market_id}/finance-context", response_model=FinanceContextResponse)
def read_market_finance_context(
    market_id: int,
    db: Session = Depends(get_db),
) -> FinanceContextResponse:
    context = get_finance_context(db, market_id)
    if context is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found.",
        )
    return context
