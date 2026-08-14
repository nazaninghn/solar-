from datetime import date as date_type
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.battery_system import BatterySystem
from app.models.energy_daily import EnergyDaily
from app.models.energy_hourly import EnergyHourly
from app.models.energy_monthly import EnergyMonthly
from app.models.financial_record import FinancialRecord
from app.modules.energy.aggregation import (
    aggregate_factory_day,
    aggregate_factory_hour,
)
from app.modules.financial.calculations import (
    calculate_grid_dependency_percent,
    calculate_solar_contribution_percent,
)


def _daily_to_dict(row: EnergyDaily) -> dict:
    # 22.39: KPIs are computed here from the row's own stored kWh
    # figures using the Financial module's existing formulas (Step 21),
    # not a second reimplementation of the same math.
    solar_coverage = calculate_solar_contribution_percent(
        row.solar_kwh, row.consumption_kwh
    )
    grid_dependency = calculate_grid_dependency_percent(
        row.grid_import_kwh, row.consumption_kwh
    )

    return {
        "factory_id": row.factory_id,
        "date": row.date,
        "solar_generation_kwh": row.solar_kwh,
        "factory_consumption_kwh": row.consumption_kwh,
        "grid_import_kwh": row.grid_import_kwh,
        "grid_export_kwh": row.grid_export_kwh,
        "battery_charge_kwh": row.battery_charge_kwh,
        "battery_discharge_kwh": row.battery_discharge_kwh,
        "solar_coverage_percent": solar_coverage,
        "grid_dependency_percent": grid_dependency,
        "peak_demand_kw": row.peak_demand_kw,
        "peak_demand_time": row.peak_demand_time,
        "peak_solar_kw": row.peak_solar_kw,
        "data_completeness": row.data_completeness,
        "data_quality": row.data_quality,
        "battery_soc": None,
        "grid_cost_today": None,
    }


def get_today_analytics(db: Session, factory_id: int) -> dict | None:
    """
    31.26's "Current Energy Status" — extends the existing /analytics/
    today (Step 22) with two live-only fields rather than forking a
    separate /energy-status endpoint: battery_soc (an instantaneous
    reading, not something daily/monthly rows have) and grid_cost_today
    (today's FinancialRecord.grid_purchase_cost, reused rather than
    recomputed — same Step 22.39 rule as the rest of this module).
    """
    today = datetime.now(timezone.utc).date()
    row = aggregate_factory_day(db, factory_id, today)

    if not row:
        return None

    result = _daily_to_dict(row)

    battery = db.scalar(
        select(BatterySystem).where(BatterySystem.factory_id == factory_id)
    )
    result["battery_soc"] = battery.state_of_charge_percent if battery else None

    financial_record = db.scalar(
        select(FinancialRecord).where(
            FinancialRecord.factory_id == factory_id, FinancialRecord.date == today
        )
    )
    result["grid_cost_today"] = (
        financial_record.grid_purchase_cost if financial_record else None
    )

    return result


def get_hourly_analytics(
    db: Session,
    factory_id: int,
    day: date_type,
) -> list[dict]:
    day_start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    rows = db.scalars(
        select(EnergyHourly)
        .where(
            EnergyHourly.factory_id == factory_id,
            EnergyHourly.hour >= day_start,
            EnergyHourly.hour < day_end,
        )
        .order_by(EnergyHourly.hour.asc())
    ).all()

    return [
        {
            "factory_id": row.factory_id,
            "timestamp": row.hour,
            "solar_generation_kwh": row.solar_kwh,
            "factory_consumption_kwh": row.consumption_kwh,
            "grid_import_kwh": row.grid_import_kwh,
            "grid_export_kwh": row.grid_export_kwh,
            "battery_charge_kwh": row.battery_charge_kwh,
            "battery_discharge_kwh": row.battery_discharge_kwh,
            "data_completeness": row.data_completeness,
            "data_quality": row.data_quality,
        }
        for row in rows
    ]


def get_daily_analytics(
    db: Session,
    factory_id: int,
    start_date: date_type,
    end_date: date_type,
    limit: int = 30,
    offset: int = 0,
) -> list[dict]:
    current = start_date
    while current <= end_date:
        existing = db.scalar(
            select(EnergyDaily).where(
                EnergyDaily.factory_id == factory_id, EnergyDaily.date == current
            )
        )
        if not existing:
            aggregate_factory_day(db, factory_id, current)
        current += timedelta(days=1)

    rows = db.scalars(
        select(EnergyDaily)
        .where(
            EnergyDaily.factory_id == factory_id,
            EnergyDaily.date >= start_date,
            EnergyDaily.date <= end_date,
        )
        .order_by(EnergyDaily.date.desc())
        .limit(limit)
        .offset(offset)
    ).all()

    return [_daily_to_dict(row) for row in rows]


def get_monthly_analytics(
    db: Session,
    factory_id: int,
    limit: int = 12,
    offset: int = 0,
) -> list[EnergyMonthly]:
    return db.scalars(
        select(EnergyMonthly)
        .where(EnergyMonthly.factory_id == factory_id)
        .order_by(EnergyMonthly.month.desc())
        .limit(limit)
        .offset(offset)
    ).all()


def backfill_analytics(
    db: Session,
    factory_id: int,
    start: datetime,
    end: datetime,
) -> dict:
    """
    22.31: re-run aggregation for a range after an outage, rather than
    leaving a gap forever. Idempotent by construction — this just calls
    the same upsert-by-unique-constraint aggregation functions already
    used by the scheduled jobs.
    """
    hours_processed = 0
    current_hour = start.replace(minute=0, second=0, microsecond=0)

    affected_days = set()

    while current_hour < end:
        aggregate_factory_hour(db, factory_id, current_hour)
        affected_days.add(current_hour.date())
        hours_processed += 1
        current_hour += timedelta(hours=1)

    days_processed = 0
    for day in affected_days:
        if aggregate_factory_day(db, factory_id, day):
            days_processed += 1

    return {"hours_processed": hours_processed, "days_processed": days_processed}
