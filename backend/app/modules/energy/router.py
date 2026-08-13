from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_accessible_factory
from app.database.session import get_db
from app.models.factory import Factory
from app.modules.energy.schemas import (
    CurrentEnergyResponse,
    EnergyHistoryResponse,
    EnergyReadingCreate,
    EnergyReadingResponse,
    EnergySummaryResponse,
)
from app.modules.energy.service import (
    create_reading,
    get_current_energy,
    get_energy_history,
    get_energy_summary,
    get_factory_energy_state,
    get_readings,
)

router = APIRouter(
    prefix="/api/v1/factories/{factory_id}/energy",
    tags=["Energy"],
)


@router.post(
    "/readings",
    response_model=EnergyReadingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_energy_reading(
    data: EnergyReadingCreate,
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    return create_reading(db=db, factory_id=factory.id, data=data)


@router.get(
    "/readings",
    response_model=list[EnergyReadingResponse],
)
def list_energy_readings(
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    return get_readings(db=db, factory_id=factory.id, start=start, end=end)


@router.get("/current", response_model=CurrentEnergyResponse)
def current_energy(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    return get_current_energy(db=db, factory_id=factory.id)


@router.get("/history", response_model=EnergyHistoryResponse)
def energy_history(
    start: datetime | None = Query(default=None, alias="from"),
    end: datetime | None = Query(default=None, alias="to"),
    resolution: str = Query(default="hour"),
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    if end is None:
        end = datetime.now(timezone.utc)

    if start is None:
        start = end - timedelta(days=1)

    data = get_energy_history(
        db=db, factory_id=factory.id, start=start, end=end, resolution=resolution
    )

    return {"resolution": resolution, "data": data}


@router.get("/summary", response_model=EnergySummaryResponse)
def energy_summary(
    period: str = Query(default="today"),
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    today = datetime.now(timezone.utc).date()

    if period == "week":
        start_date = today - timedelta(days=7)
    elif period == "month":
        start_date = today.replace(day=1)
    else:
        start_date = today

    return get_energy_summary(
        db=db, factory_id=factory.id, start_date=start_date, end_date=today
    )


@router.get("/state")
def energy_state(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    return get_factory_energy_state(db=db, factory_id=factory.id)
