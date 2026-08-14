"""
STEP 45.4-45.10: Energy KPI Calculation Engine.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.modules.advanced_analytics.models import DailyEnergyMetric, EnergyKPI

CALCULATION_VERSION = "kpi-v1"


def compute_energy_kpis(
    db: Session,
    factory_id: int,
    period_start: datetime,
    period_end: datetime,
) -> EnergyKPI:
    """Compute KPIs from daily metrics for a period."""
    dailies = (
        db.query(DailyEnergyMetric)
        .filter(
            DailyEnergyMetric.factory_id == factory_id,
            DailyEnergyMetric.date >= period_start.strftime("%Y-%m-%d"),
            DailyEnergyMetric.date <= period_end.strftime("%Y-%m-%d"),
        )
        .all()
    )

    solar = sum(d.solar_generation_kwh for d in dailies)
    consumption = sum(d.consumption_kwh for d in dailies)
    grid_import = sum(d.grid_import_kwh for d in dailies)
    grid_export = sum(d.grid_export_kwh for d in dailies)
    batt_charge = sum(d.battery_charge_kwh for d in dailies)
    batt_discharge = sum(d.battery_discharge_kwh for d in dailies)
    peak = max((d.peak_demand_kw or 0 for d in dailies), default=0)

    # 45.5: Self Consumption Rate
    solar_used_onsite = min(solar, consumption)
    self_consumption = (solar_used_onsite / solar) if solar > 0 else 0

    # 45.6: Solar Coverage Rate
    solar_coverage = (solar_used_onsite / consumption) if consumption > 0 else 0

    # 45.7: Grid Dependency
    grid_dependency = (grid_import / consumption) if consumption > 0 else 1.0

    # 45.8: Renewable Share
    total_used = consumption
    renewable = solar_used_onsite + batt_discharge
    renewable_share = (renewable / total_used) if total_used > 0 else 0

    # 45.10: Load Factor
    avg_power = (consumption / (len(dailies) * 24)) if dailies else 0
    load_factor = (avg_power / peak) if peak > 0 else 0

    kpi = EnergyKPI(
        factory_id=factory_id,
        period_start=period_start,
        period_end=period_end,
        solar_generation_kwh=round(solar, 2),
        consumption_kwh=round(consumption, 2),
        grid_import_kwh=round(grid_import, 2),
        grid_export_kwh=round(grid_export, 2),
        battery_charge_kwh=round(batt_charge, 2),
        battery_discharge_kwh=round(batt_discharge, 2),
        self_consumption_rate=round(self_consumption, 4),
        solar_coverage_rate=round(solar_coverage, 4),
        grid_dependency_rate=round(grid_dependency, 4),
        renewable_share=round(renewable_share, 4),
        peak_demand_kw=round(peak, 2),
        load_factor=round(load_factor, 4),
        calculation_version=CALCULATION_VERSION,
        created_at=datetime.now(timezone.utc),
    )

    db.merge(kpi)
    db.commit()
    db.refresh(kpi)
    return kpi
