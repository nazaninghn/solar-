"""
STEP 36.11-36.12: Rule-Based Recommendation Engine.

Generates smart recommendations based on forecast, price, battery, and constraints.
Rule-based MVP — ML optimization can replace/augment later.
"""

import json
import logging
from datetime import datetime, timedelta, timezone

from app.modules.optimization.constraints import OptimizationConstraints
from app.modules.optimization.models import (
    PRIORITY_HIGH,
    PRIORITY_MEDIUM,
    REC_BUY_GRID,
    REC_CHARGE_BATTERY,
    REC_DISCHARGE_BATTERY,
    REC_SELL_SURPLUS,
)

logger = logging.getLogger(__name__)

RULES_VERSION = "energy-rules-v1"


def generate_recommendations(
    factory_id: int,
    solar_forecast_kwh: float,
    load_forecast_kwh: float,
    battery_soc: float,
    grid_price_current: float,
    grid_price_peak: float,
    grid_price_offpeak: float,
    export_price: float,
    constraints: OptimizationConstraints | None = None,
) -> list[dict]:
    """
    36.11: Generate recommendations from current state and forecast.
    Returns list of recommendation dicts ready for DB insertion.
    """
    if constraints is None:
        constraints = OptimizationConstraints.default()

    recs: list[dict] = []
    now = datetime.now(timezone.utc)

    # --- Rule 1: Battery Charge when Solar Low + Price Peak upcoming ---
    if (
        solar_forecast_kwh < load_forecast_kwh * 0.6
        and battery_soc < 70
        and grid_price_offpeak < grid_price_peak * 0.7
    ):
        target_soc = min(constraints.battery.max_soc, 85)
        energy_needed = (target_soc - battery_soc) / 100 * constraints.battery.capacity_kwh
        savings = energy_needed * (grid_price_peak - grid_price_offpeak)

        recs.append({
            "type": REC_CHARGE_BATTERY,
            "title": "Charge battery before peak hours",
            "description": (
                f"Solar forecast is {solar_forecast_kwh:.0f} kWh (below demand). "
                f"Charge battery to {target_soc}% during off-peak to save during peak."
            ),
            "priority": PRIORITY_HIGH,
            "confidence": 0.85,
            "expected_savings": round(savings, 2),
            "savings_lower": round(savings * 0.8, 2),
            "savings_upper": round(savings * 1.2, 2),
            "start_time": now + timedelta(hours=1),
            "end_time": now + timedelta(hours=5),
            "reasoning": "Low solar forecast + high peak price = charge during off-peak",
            "reason_codes": ["LOW_SOLAR_FORECAST", "HIGH_GRID_PRICE", "BATTERY_AVAILABLE"],
            "risk_score": 0.15,
        })

    # --- Rule 2: Discharge during Peak ---
    if (
        battery_soc > 50
        and grid_price_current >= grid_price_peak * 0.9
    ):
        discharge_kwh = (battery_soc - constraints.battery.min_soc) / 100 * constraints.battery.capacity_kwh
        savings = discharge_kwh * grid_price_current * constraints.battery.efficiency

        recs.append({
            "type": REC_DISCHARGE_BATTERY,
            "title": "Use battery during peak pricing",
            "description": (
                f"Grid price is near peak (€{grid_price_current:.3f}/kWh). "
                f"Discharge battery from {battery_soc:.0f}% to reduce grid cost."
            ),
            "priority": PRIORITY_HIGH,
            "confidence": 0.88,
            "expected_savings": round(savings, 2),
            "savings_lower": round(savings * 0.85, 2),
            "savings_upper": round(savings * 1.1, 2),
            "start_time": now,
            "end_time": now + timedelta(hours=3),
            "reasoning": "Peak pricing active + battery has charge = discharge to avoid grid cost",
            "reason_codes": ["HIGH_GRID_PRICE", "BATTERY_CHARGED", "PEAK_DEMAND_RISK"],
            "risk_score": 0.1,
        })

    # --- Rule 3: Sell Surplus ---
    if (
        solar_forecast_kwh > load_forecast_kwh * 1.3
        and battery_soc > 75
        and constraints.grid.export_allowed
        and export_price > grid_price_offpeak
    ):
        surplus = solar_forecast_kwh - load_forecast_kwh
        revenue = surplus * export_price

        recs.append({
            "type": REC_SELL_SURPLUS,
            "title": "Sell surplus solar energy",
            "description": (
                f"Solar surplus of ~{surplus:.0f} kWh expected. "
                f"Battery is {battery_soc:.0f}% (sufficient). Export at €{export_price:.3f}/kWh."
            ),
            "priority": PRIORITY_MEDIUM,
            "confidence": 0.82,
            "expected_savings": 0,
            "expected_revenue": round(revenue, 2),
            "savings_lower": None,
            "savings_upper": None,
            "start_time": now + timedelta(hours=2),
            "end_time": now + timedelta(hours=8),
            "reasoning": "Solar surplus + battery full + export price attractive",
            "reason_codes": ["SOLAR_SURPLUS", "BATTERY_FULL", "HIGH_EXPORT_VALUE"],
            "risk_score": 0.12,
        })

    # --- Rule 4: Buy Grid during Off-Peak ---
    if (
        solar_forecast_kwh < load_forecast_kwh * 0.4
        and grid_price_current <= grid_price_offpeak * 1.1
        and battery_soc < 40
    ):
        buy_kwh = load_forecast_kwh - solar_forecast_kwh
        savings = buy_kwh * (grid_price_peak - grid_price_current) * 0.3  # Partial savings

        recs.append({
            "type": REC_BUY_GRID,
            "title": "Buy grid power during off-peak",
            "description": (
                f"Very low solar expected ({solar_forecast_kwh:.0f} kWh). "
                f"Current grid price is off-peak. Buy now to reduce peak cost."
            ),
            "priority": PRIORITY_MEDIUM,
            "confidence": 0.78,
            "expected_savings": round(savings, 2),
            "savings_lower": round(savings * 0.7, 2),
            "savings_upper": round(savings * 1.3, 2),
            "start_time": now,
            "end_time": now + timedelta(hours=4),
            "reasoning": "Low solar + off-peak price now = buy cheap, use later",
            "reason_codes": ["LOW_SOLAR_FORECAST", "LOW_GRID_PRICE", "BATTERY_LOW"],
            "risk_score": 0.2,
        })

    # Add common fields
    for rec in recs:
        rec["factory_id"] = factory_id
        rec["model_version"] = RULES_VERSION
        rec["rules_version"] = RULES_VERSION
        rec["reason_codes_json"] = json.dumps(rec.pop("reason_codes"))
        if "expected_revenue" not in rec:
            rec["expected_revenue"] = 0

    # Score and sort (36.21)
    for rec in recs:
        financial = rec["expected_savings"] + rec.get("expected_revenue", 0)
        rec["score"] = round(financial * rec["confidence"] * (1 - rec["risk_score"]), 2)

    recs.sort(key=lambda r: r["score"], reverse=True)

    return recs
