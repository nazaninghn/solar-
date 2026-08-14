"""STEP 37.29-37.30: Financial Engine API."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.auth.permissions import MANAGE_FINANCIAL
from app.core.dependencies import get_accessible_factory
from app.database.session import get_db
from app.models.factory import Factory
from app.models.user import User
from app.modules.finance.calculation import (
    calculate_daily_financial,
    calculate_savings_attribution,
)
from app.modules.finance.models import (
    DailyFinancialSummary,
    MonthlyFinancialSummary,
    Tariff,
)
from app.modules.finance.schemas import (
    DailyFinancialResponse,
    FinancialSummaryResponse,
    MonthlyFinancialResponse,
    SavingsAttributionResponse,
    TariffCreate,
    TariffResponse,
)
from app.modules.pipeline.models import DailyEnergySummary

router = APIRouter(
    prefix="/api/v1/factories/{factory_id}/finance",
    tags=["Financial Engine"],
)


@router.get("/summary", response_model=FinancialSummaryResponse)
def get_financial_summary(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    """37.19: Dashboard financial KPIs."""
    today_str = date.today().isoformat()
    month_str = date.today().strftime("%Y-%m")

    # Today
    today = db.query(DailyFinancialSummary).filter(
        DailyFinancialSummary.factory_id == factory.id,
        DailyFinancialSummary.date == today_str,
    ).first()

    # Monthly
    monthly = db.query(MonthlyFinancialSummary).filter(
        MonthlyFinancialSummary.factory_id == factory.id,
        MonthlyFinancialSummary.month == month_str,
    ).first()

    today_cost = today.grid_import_cost if today else 0
    today_savings = today.estimated_savings if today else 0
    monthly_savings = monthly.savings if monthly else 0
    export_rev = today.export_revenue if today else 0
    solar_val = today.solar_value if today else 0
    net = today.net_energy_benefit if today else 0
    baseline = today.baseline_cost if today else 1
    cost_reduction = ((baseline - today_cost) / baseline * 100) if baseline > 0 and today else 0

    return FinancialSummaryResponse(
        today_grid_cost=today_cost,
        today_savings=today_savings,
        monthly_savings=monthly_savings,
        export_revenue=export_rev,
        solar_value=solar_val,
        net_benefit=net,
        cost_reduction_pct=round(cost_reduction, 1),
        grid_dependency_pct=0.0,  # From pipeline KPI
        currency="EUR",
    )


@router.get("/daily", response_model=list[DailyFinancialResponse])
def get_daily_financials(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
    days: int = Query(default=30, ge=1, le=365),
):
    """37.17: Daily financial summaries."""
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    return (
        db.query(DailyFinancialSummary)
        .filter(
            DailyFinancialSummary.factory_id == factory.id,
            DailyFinancialSummary.date >= cutoff,
        )
        .order_by(DailyFinancialSummary.date.desc())
        .all()
    )


@router.get("/monthly", response_model=list[MonthlyFinancialResponse])
def get_monthly_financials(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    """37.18: Monthly financial summaries."""
    return (
        db.query(MonthlyFinancialSummary)
        .filter(MonthlyFinancialSummary.factory_id == factory.id)
        .order_by(MonthlyFinancialSummary.month.desc())
        .limit(12)
        .all()
    )


@router.get("/attribution", response_model=SavingsAttributionResponse)
def get_savings_attribution(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    """37.21: Savings breakdown by source."""
    today_str = date.today().isoformat()
    energy = db.query(DailyEnergySummary).filter(
        DailyEnergySummary.factory_id == factory.id,
        DailyEnergySummary.date == today_str,
    ).first()

    if not energy:
        return SavingsAttributionResponse(
            solar_self_consumption=0, battery_arbitrage=0,
            load_shifting=0, peak_reduction=0, export_revenue=0,
            total=0, currency="EUR",
        )

    return calculate_savings_attribution(energy)


@router.post("/calculate", response_model=DailyFinancialResponse)
def trigger_calculation(
    factory: Factory = Depends(get_accessible_factory),
    current_user: User = Depends(require_permission(MANAGE_FINANCIAL)),
    db: Session = Depends(get_db),
):
    """Manually trigger financial calculation for today."""
    return calculate_daily_financial(db=db, factory_id=factory.id, target_date=date.today())


# --- Tariffs ---

@router.get("/tariffs", response_model=list[TariffResponse])
def list_tariffs(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    return db.query(Tariff).filter(Tariff.factory_id == factory.id).all()


@router.post("/tariffs", response_model=TariffResponse, status_code=201)
def create_tariff(
    data: TariffCreate,
    factory: Factory = Depends(get_accessible_factory),
    current_user: User = Depends(require_permission(MANAGE_FINANCIAL)),
    db: Session = Depends(get_db),
):
    from datetime import datetime, timezone
    tariff = Tariff(
        factory_id=factory.id,
        name=data.name,
        type=data.type,
        currency=data.currency,
        effective_from=data.effective_from,
        effective_to=data.effective_to,
        rules_json=data.rules_json,
        created_at=datetime.now(timezone.utc),
    )
    db.add(tariff)
    db.commit()
    db.refresh(tariff)
    return tariff
