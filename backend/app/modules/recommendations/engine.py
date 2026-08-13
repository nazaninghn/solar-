from dataclasses import dataclass, field
from datetime import datetime

from app.energy.battery import calculate_battery_limits
from app.modules.recommendations.calculations import (
    calculate_battery_savings,
    calculate_sell_revenue,
)

# MVP assumption: BatterySystem has no stored round-trip efficiency yet,
# so we use the same 90% figure from the brief's own 11.20 example until
# a real per-battery efficiency spec exists.
BATTERY_ROUND_TRIP_EFFICIENCY = 0.90

# The brief's own 11.19 example ("Rule Strength = 85") doesn't derive
# this from anything either — kept as a flat MVP placeholder until rules
# have a real per-condition strength model.
RULE_STRENGTH = 85.0

# 20.14's economic-score normalization has no reference scale given —
# picked so the net_benefit figure from the brief's own 20.13 example
# (10,800,000) lands close to a 100 score.
ECONOMIC_SCORE_REFERENCE_TOMAN = 10_000_000


@dataclass
class TimeWindow:
    start: datetime
    end: datetime
    amount_kwh: float = 0.0
    price_per_kwh: float = 0.0


@dataclass
class EnergyContext:
    battery_soc: float
    battery_capacity_kwh: float
    battery_min_soc: float
    battery_max_soc: float

    solar_forecast_kwh: float
    expected_consumption_kwh: float
    expected_solar_reduction_percent: float

    current_buy_price: float
    current_sell_price: float
    price_level: str

    high_price_window: TimeWindow | None = None
    low_price_window: TimeWindow | None = None
    surplus_window: TimeWindow | None = None

    flexible_production_lines: list = field(default_factory=list)


def should_charge_battery(context: EnergyContext) -> bool:
    """
    20.7/20.11's exact three conditions: tomorrow's solar is down,
    battery isn't full, and there's a real upcoming expensive window
    worth preparing for. Deliberately doesn't also require the current
    price to be low — 20.11's own rule code doesn't check that either,
    and 20.34's Test 1 pairs a HIGH current price with an expected
    CHARGE_BATTERY result.
    """
    return (
        context.expected_solar_reduction_percent >= 20
        and context.battery_soc < context.battery_max_soc
        and context.high_price_window is not None
    )


def should_discharge_battery(context: EnergyContext) -> bool:
    return context.price_level == "high" and context.battery_soc > context.battery_min_soc


def should_buy_from_grid(context: EnergyContext) -> bool:
    """20.19: solar low, battery low, grid price low right now — top up
    from the grid while it's cheap rather than waiting until it's not."""
    return (
        context.expected_solar_reduction_percent >= 20
        and context.battery_soc <= context.battery_min_soc + 10
        and context.price_level == "low"
    )


def should_sell_to_grid(context: EnergyContext) -> bool:
    return (
        context.surplus_window is not None
        and context.battery_soc >= context.battery_max_soc
        and context.current_sell_price > 0
    )


def should_shift_load(context: EnergyContext) -> bool:
    return (
        context.price_level == "high"
        and context.expected_solar_reduction_percent >= 20
    )


def calculate_confidence(
    weather_confidence: float,
    data_quality: float,
    rule_strength: float,
) -> float:
    return round(
        weather_confidence * 0.4 + data_quality * 0.3 + rule_strength * 0.3
    )


def calculate_net_benefit(expected_benefit: float, expected_cost: float) -> float:
    """20.13, verbatim formula."""
    return round(expected_benefit - expected_cost, 2)


def calculate_recommendation_score(
    net_benefit: float,
    confidence_percent: float,
    amount_kwh: float,
    expected_consumption_kwh: float,
    hours_until_start: float,
) -> float:
    """
    20.14's weighted formula (Economic 40 / Confidence 25 / Energy
    Impact 20 / Urgency 15). None of the four sub-scores have a given
    formula in the brief (same gap as 18.24's "Decision Score" and
    19.20's confidence numbers) — each is a simple, documented MVP
    normalization rather than an arbitrary number.
    """
    economic_score = max(
        0.0, min(100.0, (net_benefit / ECONOMIC_SCORE_REFERENCE_TOMAN) * 100)
    )

    confidence_score = max(0.0, min(100.0, confidence_percent))

    energy_impact_score = (
        max(0.0, min(100.0, (amount_kwh / expected_consumption_kwh) * 100))
        if expected_consumption_kwh > 0
        else 0.0
    )

    # Full urgency at <=6h out, decaying linearly to 0 by 48h+.
    urgency_score = max(0.0, min(100.0, 100 - (hours_until_start / 48) * 100))
    if hours_until_start <= 6:
        urgency_score = 100.0

    return round(
        economic_score * 0.40
        + confidence_score * 0.25
        + energy_impact_score * 0.20
        + urgency_score * 0.15,
        2,
    )


def generate_recommendations(context: EnergyContext) -> list[dict]:
    """
    Each item includes enough raw numbers (amount_kwh, net_benefit,
    start_time/end_time) for the caller to compute confidence/score and
    persist — the economic gate from 20.12-20.13 (only recommend if
    net_benefit > 0) is enforced here, per rule, not left to the caller.
    """
    recommendations = []

    if should_charge_battery(context):
        limits = calculate_battery_limits(
            capacity_kwh=context.battery_capacity_kwh,
            soc=context.battery_soc,
            min_soc=context.battery_min_soc,
            max_soc=context.battery_max_soc,
            max_charge_kw=context.battery_capacity_kwh,  # unbounded by rate here
            max_discharge_kw=0,
        )
        energy_kwh = limits["available_for_charge_kwh"]

        cost_to_charge = energy_kwh * context.current_buy_price
        expected_saving = calculate_battery_savings(
            battery_energy_kwh=energy_kwh,
            battery_efficiency=BATTERY_ROUND_TRIP_EFFICIENCY,
            grid_price_per_kwh=context.high_price_window.price_per_kwh,
        )
        net_benefit = calculate_net_benefit(expected_saving, cost_to_charge)

        if net_benefit > 0:
            recommendations.append(
                {
                    "type": "CHARGE_BATTERY",
                    "title": "Charge battery before cloudy period",
                    "description": (
                        f"Tomorrow's solar production is expected to decrease by "
                        f"{context.expected_solar_reduction_percent:.0f}%, and "
                        f"electricity prices will be high between "
                        f"{context.high_price_window.start:%H:%M} and "
                        f"{context.high_price_window.end:%H:%M}. Charge the "
                        f"battery to {context.battery_max_soc:.0f}% tonight while "
                        f"prices are low."
                    ),
                    "estimated_savings": expected_saving,
                    "estimated_revenue": 0.0,
                    "net_benefit": net_benefit,
                    "amount_kwh": energy_kwh,
                    "start_time": None,
                    "end_time": context.high_price_window.start,
                }
            )

    if should_discharge_battery(context):
        limits = calculate_battery_limits(
            capacity_kwh=context.battery_capacity_kwh,
            soc=context.battery_soc,
            min_soc=context.battery_min_soc,
            max_soc=context.battery_max_soc,
            max_charge_kw=0,
            max_discharge_kw=context.battery_capacity_kwh,
        )
        energy_kwh = limits["available_for_discharge_kwh"]

        savings = calculate_battery_savings(
            battery_energy_kwh=energy_kwh,
            battery_efficiency=BATTERY_ROUND_TRIP_EFFICIENCY,
            grid_price_per_kwh=context.current_buy_price,
        )
        # No real cost model for discharging stored energy yet (battery
        # wear/degradation isn't tracked) — treated as zero-cost, so
        # net_benefit collapses to the savings themselves.
        net_benefit = calculate_net_benefit(savings, 0)

        if net_benefit > 0:
            recommendations.append(
                {
                    "type": "DISCHARGE_BATTERY",
                    "title": "Use battery during peak price",
                    "description": (
                        "Grid electricity prices are currently high. Using "
                        "stored energy can reduce grid costs."
                    ),
                    "estimated_savings": savings,
                    "estimated_revenue": 0.0,
                    "net_benefit": net_benefit,
                    "amount_kwh": energy_kwh,
                    "start_time": None,
                    "end_time": None,
                }
            )

    if should_buy_from_grid(context) and context.low_price_window is not None:
        limits = calculate_battery_limits(
            capacity_kwh=context.battery_capacity_kwh,
            soc=context.battery_soc,
            min_soc=context.battery_min_soc,
            max_soc=context.battery_max_soc,
            max_charge_kw=context.battery_capacity_kwh,
            max_discharge_kw=0,
        )
        energy_kwh = limits["available_for_charge_kwh"]
        cost_now = energy_kwh * context.low_price_window.price_per_kwh

        # Reference "what it would otherwise cost": the known upcoming
        # high-price window if one exists, else a flat 20% markup over
        # today's price. Using current_buy_price here would be wrong —
        # "now" often *is* inside the low window itself, which would
        # trivially net zero benefit against its own price.
        reference_price = (
            context.high_price_window.price_per_kwh
            if context.high_price_window
            else context.current_buy_price * 1.2
        )
        avoided_cost = energy_kwh * reference_price
        net_benefit = calculate_net_benefit(avoided_cost, cost_now)

        if net_benefit > 0:
            recommendations.append(
                {
                    "type": "BUY_FROM_GRID",
                    "title": "Buy grid energy while it's cheap",
                    "description": (
                        f"Electricity prices are low between "
                        f"{context.low_price_window.start:%H:%M} and "
                        f"{context.low_price_window.end:%H:%M}. Buying part of "
                        f"the battery's charge during this window is cheaper "
                        f"than later."
                    ),
                    "estimated_savings": net_benefit,
                    "estimated_revenue": 0.0,
                    "net_benefit": net_benefit,
                    "amount_kwh": energy_kwh,
                    "start_time": context.low_price_window.start,
                    "end_time": context.low_price_window.end,
                }
            )

    if should_sell_to_grid(context):
        surplus_kwh = context.surplus_window.amount_kwh
        revenue = calculate_sell_revenue(
            surplus_kwh=surplus_kwh,
            sell_price_per_kwh=context.surplus_window.price_per_kwh,
        )
        net_benefit = calculate_net_benefit(revenue, 0)

        if net_benefit > 0:
            recommendations.append(
                {
                    "type": "SELL_TO_GRID",
                    "title": "Sell excess solar energy",
                    "description": (
                        f"Between {context.surplus_window.start:%H:%M} and "
                        f"{context.surplus_window.end:%H:%M}, solar generation "
                        f"is expected to exceed factory consumption, and the "
                        f"battery is already full."
                    ),
                    "estimated_savings": 0.0,
                    "estimated_revenue": revenue,
                    "net_benefit": net_benefit,
                    "amount_kwh": surplus_kwh,
                    "start_time": context.surplus_window.start,
                    "end_time": context.surplus_window.end,
                }
            )

    if should_shift_load(context):
        if context.flexible_production_lines:
            line = context.flexible_production_lines[0]
            hours = line.minimum_run_time_hours or 4
            amount_kwh = line.power_kw * hours
            price_spread = max(
                0.0, context.current_buy_price - context.current_sell_price
            )
            savings = round(amount_kwh * price_spread, 2)
            net_benefit = calculate_net_benefit(savings, 0)
            description = (
                f"Shifting {line.name} to a lower-price, higher-solar window "
                f"could save an estimated amount based on {hours:.0f} hours "
                f"of runtime."
            )
        else:
            amount_kwh = 0.0
            savings = 0.0
            net_benefit = 0.0
            description = (
                "Move flexible production loads away from high electricity "
                "price periods. No flexible production lines are configured "
                "yet, so no specific savings estimate is available."
            )

        if net_benefit > 0 or not context.flexible_production_lines:
            recommendations.append(
                {
                    "type": "SHIFT_LOAD",
                    "title": "Shift flexible production",
                    "description": description,
                    "estimated_savings": savings,
                    "estimated_revenue": 0.0,
                    "net_benefit": net_benefit,
                    "amount_kwh": amount_kwh,
                    "start_time": None,
                    "end_time": None,
                }
            )

    return recommendations
