"""
STEP 34.23: KPI Calculation Engine.

Computes energy KPIs from daily summaries:
- Solar Coverage
- Grid Dependency
- Battery Utilization
- Peak Demand
- Savings
"""

from app.modules.pipeline.models import DailyEnergySummary
from app.modules.pipeline.schemas import EnergyKPIResponse


def compute_kpis(summary: DailyEnergySummary) -> EnergyKPIResponse:
    """34.23: Calculate KPIs from a daily energy summary."""

    consumption = summary.factory_consumption_kwh or 1.0  # Avoid division by zero

    # Solar Coverage = Solar used by factory / Total consumption
    solar_self_use = min(summary.solar_generation_kwh, consumption)
    solar_coverage = solar_self_use / consumption if consumption > 0 else 0.0

    # Grid Dependency = Grid Import / Consumption
    grid_dependency = summary.grid_import_kwh / consumption if consumption > 0 else 1.0

    # Battery Utilization (simplified: discharge/consumption ratio)
    battery_utilization = summary.battery_discharge_kwh / consumption if consumption > 0 else 0.0

    return EnergyKPIResponse(
        solar_coverage=round(solar_coverage, 4),
        grid_dependency=round(grid_dependency, 4),
        battery_utilization=round(battery_utilization, 4),
        peak_demand_kw=summary.peak_power_kw or 0.0,
        total_savings=summary.estimated_savings,
        export_revenue=0.0,  # Computed by financial engine
        data_quality_score=summary.data_quality_score,
    )
