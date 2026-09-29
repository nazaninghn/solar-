"""Failure prediction API."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_accessible_factory, get_current_user
from app.database.session import get_db
from app.models.device import Device
from app.models.factory import Factory
from app.models.user import User
from app.modules.failure_prediction.ml_model import get_model
from app.modules.failure_prediction.models import FailureEvent, FailureRiskAssessment
from app.modules.failure_prediction.schemas import (
    AssessmentResponse,
    DeviceRiskResponse,
    FailureEventCreate,
    FailureEventResponse,
    ModelInfoResponse,
    RiskHistoryPoint,
    RiskOverviewResponse,
)
from app.modules.failure_prediction.service import (
    assess_factory,
    fetch_weather,
    latest_assessments,
)

router = APIRouter(
    prefix="/api/v1/factories/{factory_id}/failure-prediction",
    tags=["Failure Prediction"],
)


def _get_device(db: Session, factory: Factory, device_id: int) -> Device:
    device = db.get(Device, device_id)
    if device is None or device.factory_id != factory.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return device


def _overview(db: Session, factory: Factory) -> RiskOverviewResponse:
    rows = latest_assessments(db, factory.id)
    counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0, "UNASSESSED": 0}
    devices = []
    for device, assessment in rows:
        counts[assessment.risk_level if assessment else "UNASSESSED"] += 1
        devices.append(DeviceRiskResponse(
            device_id=device.id,
            device_name=device.name,
            device_type=device.device_type,
            status=device.status,
            assessment=AssessmentResponse.model_validate(assessment) if assessment else None,
        ))
    # Highest risk first — the page is a triage list.
    devices.sort(key=lambda d: -(d.assessment.risk_score if d.assessment else -1))
    stamps = [a.assessed_at for _, a in rows if a]
    return RiskOverviewResponse(
        factory_id=factory.id,
        assessed_at=max(stamps) if stamps else None,
        counts=counts,
        devices=devices,
    )


@router.get("/overview", response_model=RiskOverviewResponse)
def overview(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    return _overview(db, factory)


@router.post("/assess", response_model=RiskOverviewResponse)
async def assess_now(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    """Run an assessment immediately instead of waiting for the
    15-minute job. Alerts fire exactly as they would from the job."""
    weather = await fetch_weather(factory)
    assess_factory(db, factory, weather)
    return _overview(db, factory)


@router.get("/devices/{device_id}/history", response_model=list[RiskHistoryPoint])
def device_history(
    device_id: int,
    days: int = Query(default=7, ge=1, le=90),
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    _get_device(db, factory, device_id)
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = db.scalars(
        select(FailureRiskAssessment)
        .where(FailureRiskAssessment.device_id == device_id, FailureRiskAssessment.assessed_at >= since)
        .order_by(FailureRiskAssessment.assessed_at.asc())
    ).all()
    return [
        RiskHistoryPoint(
            assessed_at=r.assessed_at,
            risk_score=r.risk_score,
            risk_level=r.risk_level,
            failure_probability=r.failure_probability,
        )
        for r in rows
    ]


@router.get("/events", response_model=list[FailureEventResponse])
def list_events(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(FailureEvent)
        .where(FailureEvent.factory_id == factory.id)
        .order_by(FailureEvent.occurred_at.desc())
    ).all()


@router.post("/events", response_model=FailureEventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    data: FailureEventCreate,
    factory: Factory = Depends(get_accessible_factory),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record a real failure — the ground truth every threshold and any
    future site-specific model gets checked against."""
    _get_device(db, factory, data.device_id)
    event = FailureEvent(
        factory_id=factory.id,
        reported_by_user_id=user.id,
        created_at=datetime.now(timezone.utc),
        **data.model_dump(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.get("/model", response_model=ModelInfoResponse)
def model_info(factory: Factory = Depends(get_accessible_factory)):
    meta = get_model().meta
    binary, fault = meta["binary"], meta["fault_type"]
    return ModelInfoResponse(
        version=binary["version"],
        source=meta["source"],
        label=binary["label"],
        horizon_minutes=binary["horizon_minutes"],
        threshold=binary["threshold"],
        daylight_irradiance_w_m2=binary["daylight_irradiance_w_m2"],
        test_metrics=binary["test_metrics"],
        lead_time=binary["lead_time"],
        fault_type_version=fault["version"],
        fault_types=[v for k, v in fault["fault_names"].items() if k != "0"],
        fault_type_macro_f1=fault["test_macro_f1"],
        limitations=[
            "Trained on one ~1 kW PV system (PVDAQ system 10); inputs are transferred by capacity and per-unit scaling, not retrained per site.",
            "Training labels are physics-rule pseudo-labels, not confirmed failures.",
            "Precision on held-out days is about 0.38: treat it as an early warning, not a diagnosis.",
            "Weather GHI is used when no plane-of-array irradiance sensor reports; this is a proxy.",
            "Only PV inverters are scored by the model; batteries, meters and comms use rule indicators.",
        ],
    )
