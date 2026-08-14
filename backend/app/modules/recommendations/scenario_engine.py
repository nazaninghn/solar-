from dataclasses import dataclass

from app.modules.financial.calculations import get_battery_degradation_rate
from app.modules.financial.service import BATTERY_DEGRADATION_RATE
from app.modules.recommendations.engine import EnergyContext


@dataclass
class ScenarioResult:
    name: str
    applicable: bool
    total_cost: float
    grid_import_kwh: float
    grid_export_kwh: float
    battery_charge_kwh: float
    battery_discharge_kwh: float
    load_shifted_kwh: float
    explanation: str


def _grid_only_cost(imbalance_kwh: float, context: EnergyContext) -> float:
    if imbalance_kwh >= 0:
        return round(imbalance_kwh * context.current_buy_price, 2)
    return round(imbalance_kwh * context.current_sell_price, 2)


def _battery_available_discharge_kwh(context: EnergyContext) -> float:
    return max(
        0.0,
        context.battery_capacity_kwh
        * (context.battery_soc - context.battery_min_soc)
        / 100,
    )


def _battery_available_charge_kwh(context: EnergyContext) -> float:
    return max(
        0.0,
        context.battery_capacity_kwh
        * (context.battery_max_soc - context.battery_soc)
        / 100,
    )


def _battery_scenario(
    imbalance_kwh: float, context: EnergyContext, degradation_rate: float
) -> ScenarioResult:
    """29.7's battery safety limits apply directly here — the battery
    can never be asked to discharge below battery_min_soc or charge
    above battery_max_soc, so "available" is always capped by those,
    not by the full nameplate capacity."""
    if imbalance_kwh >= 0:
        available = _battery_available_discharge_kwh(context)
        covered = min(imbalance_kwh, available)
        remaining_grid = imbalance_kwh - covered
        cost = round(
            remaining_grid * context.current_buy_price + covered * degradation_rate, 2
        )

        return ScenarioResult(
            name="BATTERY",
            applicable=covered > 0,
            total_cost=cost,
            grid_import_kwh=remaining_grid,
            grid_export_kwh=0.0,
            battery_charge_kwh=0.0,
            battery_discharge_kwh=covered,
            load_shifted_kwh=0.0,
            explanation=(
                f"Battery discharges {covered:.1f} kWh (capped by min SOC); "
                f"remaining {remaining_grid:.1f} kWh bought from grid."
            ),
        )

    surplus = -imbalance_kwh
    room = _battery_available_charge_kwh(context)
    absorbed = min(surplus, room)
    remaining_export = surplus - absorbed
    cost = round(
        -remaining_export * context.current_sell_price + absorbed * degradation_rate, 2
    )

    return ScenarioResult(
        name="BATTERY",
        applicable=absorbed > 0,
        total_cost=cost,
        grid_import_kwh=0.0,
        grid_export_kwh=remaining_export,
        battery_charge_kwh=absorbed,
        battery_discharge_kwh=0.0,
        load_shifted_kwh=0.0,
        explanation=(
            f"Battery charges {absorbed:.1f} kWh (capped by max SOC); "
            f"remaining {remaining_export:.1f} kWh exported to grid."
        ),
    )


def _shiftable_kwh(context: EnergyContext) -> float:
    # 29.13-29.14: a flexible line with no minimum_run_time_hours is
    # treated as shiftable for one hour — the same window granularity
    # the rest of this scenario comparison operates at.
    return sum(
        line.power_kw * (line.minimum_run_time_hours or 1.0)
        for line in context.flexible_production_lines
    )


def _load_shift_scenario(imbalance_kwh: float, context: EnergyContext) -> ScenarioResult:
    if imbalance_kwh <= 0 or not context.flexible_production_lines:
        return ScenarioResult(
            name="LOAD_SHIFT",
            applicable=False,
            total_cost=_grid_only_cost(imbalance_kwh, context),
            grid_import_kwh=max(0.0, imbalance_kwh),
            grid_export_kwh=max(0.0, -imbalance_kwh),
            battery_charge_kwh=0.0,
            battery_discharge_kwh=0.0,
            load_shifted_kwh=0.0,
            explanation="Not applicable: no deficit, or no flexible production lines configured.",
        )

    shiftable = _shiftable_kwh(context)
    shifted = min(imbalance_kwh, shiftable)
    remaining_grid = imbalance_kwh - shifted
    cost = round(remaining_grid * context.current_buy_price, 2)

    return ScenarioResult(
        name="LOAD_SHIFT",
        applicable=shifted > 0,
        total_cost=cost,
        grid_import_kwh=remaining_grid,
        grid_export_kwh=0.0,
        battery_charge_kwh=0.0,
        battery_discharge_kwh=0.0,
        load_shifted_kwh=shifted,
        explanation=(
            f"{shifted:.1f} kWh of flexible production shifted out of this window; "
            f"remaining {remaining_grid:.1f} kWh bought from grid."
        ),
    )


def _combined_scenario(
    imbalance_kwh: float, context: EnergyContext, degradation_rate: float
) -> ScenarioResult:
    """29.23's "ترکیبی" (combined) scenario: battery first, then load
    shifting, then whatever's left goes to the grid. For a surplus,
    there's nothing to shift into a surplus window in this model, so
    COMBINED collapses to the same answer as BATTERY."""
    if imbalance_kwh <= 0:
        result = _battery_scenario(imbalance_kwh, context, degradation_rate)
        return ScenarioResult(**{**result.__dict__, "name": "COMBINED"})

    battery_available = _battery_available_discharge_kwh(context)
    battery_covered = min(imbalance_kwh, battery_available)
    after_battery = imbalance_kwh - battery_covered

    shiftable = _shiftable_kwh(context)
    shifted = min(after_battery, shiftable)
    remaining_grid = after_battery - shifted

    cost = round(
        remaining_grid * context.current_buy_price + battery_covered * degradation_rate,
        2,
    )

    return ScenarioResult(
        name="COMBINED",
        applicable=True,
        total_cost=cost,
        grid_import_kwh=remaining_grid,
        grid_export_kwh=0.0,
        battery_charge_kwh=0.0,
        battery_discharge_kwh=battery_covered,
        load_shifted_kwh=shifted,
        explanation=(
            f"Battery covers {battery_covered:.1f} kWh, {shifted:.1f} kWh of flexible "
            f"load shifted, remaining {remaining_grid:.1f} kWh bought from grid."
        ),
    )


def evaluate_energy_scenarios(
    context: EnergyContext,
    factory_battery_degradation_override: float | None = None,
) -> list[ScenarioResult]:
    """
    29.23-29.24: compares DO_NOTHING/GRID/BATTERY/LOAD_SHIFT/COMBINED
    for the current solar-vs-consumption imbalance and computes each
    scenario's total cost (grid purchase cost + battery degradation
    cost - export revenue), respecting battery SOC limits (29.7) and
    flexible-line availability (29.13-29.14). Additive to the existing
    rule-based engine, not a replacement — each scenario here is a
    strict subset/composition of what the rules already independently
    decide; this exists to make "why this action, not another" an
    explicit, auditable comparison (29.18) rather than changing what
    gets recommended.
    """
    imbalance_kwh = context.expected_consumption_kwh - context.solar_forecast_kwh
    degradation_rate = get_battery_degradation_rate(
        factory_battery_degradation_override,
        context.current_buy_price,
        BATTERY_DEGRADATION_RATE,
    )

    grid_cost = _grid_only_cost(imbalance_kwh, context)
    grid_import = max(0.0, imbalance_kwh)
    grid_export = max(0.0, -imbalance_kwh)

    do_nothing = ScenarioResult(
        name="DO_NOTHING",
        applicable=True,
        total_cost=grid_cost,
        grid_import_kwh=grid_import,
        grid_export_kwh=grid_export,
        battery_charge_kwh=0.0,
        battery_discharge_kwh=0.0,
        load_shifted_kwh=0.0,
        explanation="No action taken; the full imbalance is bought from or sold to the grid.",
    )

    # 29.23 names DO_NOTHING and GRID as separate scenarios; in this
    # model they're numerically identical — the grid is the only
    # passive absorber of an imbalance when no other action is taken.
    grid_only = ScenarioResult(
        name="GRID",
        applicable=True,
        total_cost=grid_cost,
        grid_import_kwh=grid_import,
        grid_export_kwh=grid_export,
        battery_charge_kwh=0.0,
        battery_discharge_kwh=0.0,
        load_shifted_kwh=0.0,
        explanation="Same outcome as Do Nothing — the grid is the only passive absorber of an imbalance.",
    )

    return [
        do_nothing,
        grid_only,
        _battery_scenario(imbalance_kwh, context, degradation_rate),
        _load_shift_scenario(imbalance_kwh, context),
        _combined_scenario(imbalance_kwh, context, degradation_rate),
    ]


def rank_scenarios(scenarios: list[ScenarioResult]) -> list[ScenarioResult]:
    """29.24: the best scenario is the cheapest *applicable* one."""
    applicable = [s for s in scenarios if s.applicable]

    return sorted(applicable or scenarios, key=lambda s: s.total_cost)
