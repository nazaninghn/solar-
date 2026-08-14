"""
STEP 37.8-37.21: Financial Calculation Engine.

Computes costs, revenue, savings, and attribution from energy data and tariffs.
"""

import logging
from datetime import date

from sqlalchemy.orm import Session

from app.modules.finance.models import (
    DailyFinancialSummary,
)
from app.modules.pipeline.models import DailyEnergySummary

logger = logging.getLogger(__name__)

CALCULATION_VERSION = "v1"

# Default prices (used when no tariff configured) — MVP placeholder
DEFAULT_IMPORT_PRICE = 0.18  # EUR/kWh
DEFAULT_EXPORT_PRICE = 0.08  # EUR/kWh
DEFAULT_BATTERY_DEGRADATION = 0.02  # EUR/kWh throughput


def calculate_daily_financial(
    db: Session,
    factory_id: int,
    target_date: date,
    import_price: float | None = None,
    export_price: float | None = None,
) -> DailyFinancialSummary:
    """
    37.8-37.15: Calculate daily financials from energy summary.
    """
    date_str = target_date.isoformat()
    price_import = import_price or DEFAULT_IMPORT_PRICE
    price_export = export_price or DEFAULT_EXPORT_PRICE

    # Get energy summary
    energy = (
        db.query(DailyEnergySummary)
        .filter(
            DailyEnergySummary.factory_id == factory_id,
            DailyEnergySummary.date == date_str,
        )
        .first()
    )

    if not energy:
        # No energy data — return zero summary
        return DailyFinancialSummary(
            factory_id=factory_id,
            date=date_str,
            grid_import_cost=0,
            export_revenue=0,
            solar_value=0,
            battery_cost=0,
            total_energy_cost=0,
            baseline_cost=0,
            estimated_savings=0,
            net_energy_benefit=0,
            currency="EUR",
            calculation_version=CALCULATION_VERSION,
            data_quality="NO_DATA",
        )

    # 37.8: Grid Import Cost
    grid_cost = energy.grid_import_kwh * price_import

    # 37.9: Export Revenue
    export_rev = energy.grid_export_kwh * price_export

    # 37.10: Solar Value (avoided grid cost)
    solar_self_consumed = min(
        energy.solar_generation_kwh,
        energy.factory_consumption_kwh
    )
    solar_value = solar_self_consumed * price_import

    # 37.11: Battery Cost (degradation)
    battery_throughput = energy.battery_charge_kwh + energy.battery_discharge_kwh
    battery_cost = battery_throughput * DEFAULT_BATTERY_DEGRADATION

    # Total actual energy cost
    total_cost = grid_cost + battery_cost - export_rev

    # 37.15: Baseline (Grid-Only) — what it would cost without solar/battery
    baseline_cost = energy.factory_consumption_kwh * price_import

    # 37.15: Savings
    savings = max(0, baseline_cost - total_cost)

    # Net benefit
    net_benefit = savings + export_rev

    summary = DailyFinancialSummary(
        factory_id=factory_id,
        date=date_str,
        grid_import_cost=round(grid_cost, 2),
        export_revenue=round(export_rev, 2),
        solar_value=round(solar_value, 2),
        battery_cost=round(battery_cost, 2),
        total_energy_cost=round(total_cost, 2),
        baseline_cost=round(baseline_cost, 2),
        estimated_savings=round(savings, 2),
        net_energy_benefit=round(net_benefit, 2),
        currency="EUR",
        calculation_version=CALCULATION_VERSION,
        data_quality=energy.data_quality,
    )

    db.merge(summary)
    db.commit()
    db.refresh(summary)
    return summary


def calculate_savings_attribution(
    energy: DailyEnergySummary,
    import_price: float = DEFAULT_IMPORT_PRICE,
    export_price: float = DEFAULT_EXPORT_PRICE,
) -> dict:
    """37.21: Break down savings by source."""
    solar_self = min(energy.solar_generation_kwh, energy.factory_consumption_kwh)
    solar_savings = solar_self * import_price

    # Battery arbitrage (simplified: discharge value - charge cost)
    battery_savings = energy.battery_discharge_kwh * import_price * 0.3  # Approximate

    # Export revenue
    export_rev = energy.grid_export_kwh * export_price

    # Peak reduction (simplified)
    peak_savings = 0.0  # Would need peak demand data

    total = solar_savings + battery_savings + export_rev + peak_savings

    return {
        "solar_self_consumption": round(solar_savings, 2),
        "battery_arbitrage": round(battery_savings, 2),
        "load_shifting": 0.0,
        "peak_reduction": round(peak_savings, 2),
        "export_revenue": round(export_rev, 2),
        "total": round(total, 2),
        "currency": "EUR",
    }


def calculate_roi(
    monthly_benefit: float,
    initial_investment: float,
) -> dict:
    """37.40-37.41: Simple ROI and payback calculation."""
    if initial_investment <= 0:
        return {
            "initial_investment": 0,
            "annual_benefit": monthly_benefit * 12,
            "payback_months": None,
            "roi_pct": None,
            "currency": "EUR",
        }

    annual = monthly_benefit * 12
    payback = initial_investment / monthly_benefit if monthly_benefit > 0 else None
    roi_pct = (annual / initial_investment) * 100 if initial_investment > 0 else None

    return {
        "initial_investment": round(initial_investment, 2),
        "annual_benefit": round(annual, 2),
        "payback_months": round(payback, 1) if payback else None,
        "roi_pct": round(roi_pct, 1) if roi_pct else None,
        "currency": "EUR",
    }
