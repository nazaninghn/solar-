"""
STEP 50.21-50.29: Energy Reconciliation Engine.

Validates that energy flows balance within tolerance.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.modules.data_integrity.models import EnergyReconciliation
from app.modules.pipeline.models import DailyEnergySummary

logger = logging.getLogger(__name__)


def reconcile_daily_energy(
    db: Session,
    organization_id: int,
    factory_id: int,
    date_str: str,
    tolerance_pct: float = 10.0,
) -> EnergyReconciliation:
    """
    50.25: Check energy balance for a factory on a given date.
    Generation + Import + Discharge ≈ Consumption + Export + Charge + Losses
    """
    summary = db.query(DailyEnergySummary).filter(
        DailyEnergySummary.factory_id == factory_id,
        DailyEnergySummary.date == date_str,
    ).first()

    now = datetime.now(timezone.utc)

    if not summary:
        return EnergyReconciliation(
            organization_id=organization_id,
            factory_id=factory_id,
            period_start=now,
            period_end=now,
            status="FAILED",
            difference_kwh=0,
            created_at=now,
        )

    supply = summary.solar_generation_kwh + summary.grid_import_kwh + summary.battery_discharge_kwh
    demand = summary.factory_consumption_kwh + summary.grid_export_kwh + summary.battery_charge_kwh

    difference = abs(supply - demand)
    max_flow = max(supply, demand, 1)
    tolerance = max_flow * (tolerance_pct / 100.0)

    if difference <= tolerance:
        status = "MATCHED"
    elif difference <= tolerance * 2:
        status = "WARNING"
    else:
        status = "MISMATCH"

    recon = EnergyReconciliation(
        organization_id=organization_id,
        factory_id=factory_id,
        period_start=now,
        period_end=now,
        generation_kwh=summary.solar_generation_kwh,
        consumption_kwh=summary.factory_consumption_kwh,
        grid_import_kwh=summary.grid_import_kwh,
        grid_export_kwh=summary.grid_export_kwh,
        battery_charge_kwh=summary.battery_charge_kwh,
        battery_discharge_kwh=summary.battery_discharge_kwh,
        difference_kwh=round(difference, 2),
        tolerance_kwh=round(tolerance, 2),
        status=status,
        created_at=now,
    )
    db.add(recon)
    db.commit()
    db.refresh(recon)

    if status == "MISMATCH":
        logger.warning(
            f"Energy reconciliation MISMATCH factory={factory_id} date={date_str} "
            f"supply={supply:.1f} demand={demand:.1f} diff={difference:.1f}"
        )

    return recon
