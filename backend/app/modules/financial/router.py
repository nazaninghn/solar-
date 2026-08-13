from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_accessible_factory
from app.database.session import get_db
from app.models.factory import Factory
from app.modules.financial.schemas import (
    FinancialKPIResponse,
    FinancialSummaryResponse,
    FinancialTransactionResponse,
    MonthlyFinancialSummary,
)
from app.modules.financial.service import (
    get_financial_kpis,
    get_monthly_history,
    get_period_summary,
    get_transactions,
)

router = APIRouter(
    prefix="/api/v1/factories/{factory_id}/financial",
    tags=["Financial"],
)


@router.get("/summary", response_model=FinancialSummaryResponse)
def financial_summary(
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    if start is None or end is None:
        today = datetime.now(timezone.utc).date()
        start = today.replace(day=1)
        end = today

    return get_period_summary(
        db=db, factory_id=factory.id, start_date=start, end_date=end
    )


@router.get("/monthly", response_model=list[MonthlyFinancialSummary])
def financial_monthly_history(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    return get_monthly_history(db=db, factory_id=factory.id)


@router.get("/kpis", response_model=FinancialKPIResponse)
def financial_kpis(
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    if start is None or end is None:
        today = datetime.now(timezone.utc).date()
        start = today.replace(day=1)
        end = today

    return get_financial_kpis(db=db, factory=factory, start_date=start, end_date=end)


@router.get("/transactions", response_model=list[FinancialTransactionResponse])
def financial_transactions(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    type: str | None = Query(default=None),
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    if end_date is None:
        end_date = datetime.now(timezone.utc).date()
    if start_date is None:
        start_date = end_date - timedelta(days=30)

    start = datetime(start_date.year, start_date.month, start_date.day, tzinfo=timezone.utc)
    end = datetime(
        end_date.year, end_date.month, end_date.day, 23, 59, 59, tzinfo=timezone.utc
    )

    return get_transactions(
        db=db, factory_id=factory.id, start=start, end=end, transaction_type=type
    )
