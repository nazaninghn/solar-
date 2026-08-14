"""STEP 50: Data Integrity & Reconciliation API."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_accessible_factory, get_current_user
from app.database.session import get_db
from app.models.device import Device
from app.models.factory import Factory
from app.models.user import User
from app.modules.data_integrity.models import (
    DataAnomaly,
    DataCorrection,
    DataQualityRecord,
    EnergyReconciliation,
)
from app.modules.data_integrity.reconciliation import reconcile_daily_energy
from app.modules.data_integrity.schemas import (
    DataAnomalyResponse,
    DataCorrectionResponse,
    DataQualityRecordResponse,
    FactoryDataHealthResponse,
    ReconciliationResponse,
)

router = APIRouter(
    prefix="/api/v1/factories/{factory_id}/data-integrity",
    tags=["Data Integrity"],
)


@router.get("/quality", response_model=list[DataQualityRecordResponse])
def list_quality_records(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
    limit: int = Query(default=50, le=200),
):
    """50.18: Data quality records per device."""
    device_ids = [d.id for d in db.query(Device.id).filter(Device.factory_id == factory.id).all()]
    if not device_ids:
        return []
    return (
        db.query(DataQualityRecord)
        .filter(DataQualityRecord.device_id.in_(device_ids))
        .order_by(DataQualityRecord.period_start.desc())
        .limit(limit)
        .all()
    )


@router.get("/reconciliation", response_model=list[ReconciliationResponse])
def list_reconciliations(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    """50.27: Energy reconciliation history."""
    return (
        db.query(EnergyReconciliation)
        .filter(EnergyReconciliation.factory_id == factory.id)
        .order_by(EnergyReconciliation.created_at.desc())
        .limit(30)
        .all()
    )


@router.post("/reconciliation/run", response_model=ReconciliationResponse)
def run_reconciliation(
    factory: Factory = Depends(get_accessible_factory),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """50.26: Trigger reconciliation for today."""
    today_str = date.today().isoformat()
    return reconcile_daily_energy(
        db=db,
        organization_id=current_user.organization_id,
        factory_id=factory.id,
        date_str=today_str,
    )


@router.get("/anomalies", response_model=list[DataAnomalyResponse])
def list_anomalies(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
    status: str | None = Query(default=None),
):
    """50.31: Data anomalies."""
    query = db.query(DataAnomaly).filter(DataAnomaly.factory_id == factory.id)
    if status:
        query = query.filter(DataAnomaly.status == status)
    return query.order_by(DataAnomaly.detected_at.desc()).limit(50).all()


@router.get("/corrections", response_model=list[DataCorrectionResponse])
def list_corrections(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    """50.34: Data correction audit trail."""
    return (
        db.query(DataCorrection)
        .filter(DataCorrection.factory_id == factory.id)
        .order_by(DataCorrection.created_at.desc())
        .limit(50)
        .all()
    )


@router.get("/health", response_model=FactoryDataHealthResponse)
def factory_data_health(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    """50.42: Factory data health overview."""
    devices = db.query(Device).filter(Device.factory_id == factory.id, Device.is_active == True).all()
    total = len(devices)
    online = sum(1 for d in devices if d.status == "ONLINE")

    anomaly_count = db.query(DataAnomaly).filter(
        DataAnomaly.factory_id == factory.id, DataAnomaly.status == "DETECTED"
    ).count()

    last_recon = (
        db.query(EnergyReconciliation)
        .filter(EnergyReconciliation.factory_id == factory.id)
        .order_by(EnergyReconciliation.created_at.desc())
        .first()
    )

    quality_pct = (online / total * 100) if total > 0 else 0
    missing_pct = ((total - online) / total * 100) if total > 0 else 0

    return FactoryDataHealthResponse(
        factory_id=factory.id,
        total_devices=total,
        online_devices=online,
        data_quality_pct=round(quality_pct, 1),
        missing_pct=round(missing_pct, 1),
        anomaly_count=anomaly_count,
        reconciliation_status=last_recon.status if last_recon else "NONE",
    )
