def calculate_solar_savings(
    solar_used_kwh: float,
    grid_price_per_kwh: float,
) -> float:
    return round(solar_used_kwh * grid_price_per_kwh, 2)


def calculate_grid_cost(
    grid_energy_kwh: float,
    grid_price_per_kwh: float,
) -> float:
    return round(grid_energy_kwh * grid_price_per_kwh, 2)


def calculate_battery_savings(
    battery_energy_kwh: float,
    efficiency: float,
    grid_price_per_kwh: float,
) -> float:
    usable_energy = battery_energy_kwh * efficiency

    return round(usable_energy * grid_price_per_kwh, 2)


def calculate_energy_sales(
    sold_energy_kwh: float,
    sell_price_per_kwh: float,
) -> float:
    return round(sold_energy_kwh * sell_price_per_kwh, 2)


def calculate_total_savings(
    solar_savings: float,
    battery_savings: float,
    energy_sales_revenue: float,
) -> float:
    return round(solar_savings + battery_savings + energy_sales_revenue, 2)


def calculate_net_energy_cost(
    grid_purchase_cost: float,
    total_savings: float,
) -> float:
    return round(grid_purchase_cost - total_savings, 2)


def calculate_cost_reduction_percent(
    baseline_cost: float,
    actual_cost: float,
) -> float:
    if baseline_cost <= 0:
        return 0.0

    return round(((baseline_cost - actual_cost) / baseline_cost) * 100, 2)


def calculate_change_percent(current: float, previous: float) -> float:
    """
    Not in the brief — needed for FinancialSummaryResponse.savings_change_percent
    (12.14), which the brief names but never derives a formula for.
    Standard period-over-period percent change.
    """
    if previous <= 0:
        return 0.0

    return round(((current - previous) / previous) * 100, 2)


def calculate_battery_degradation_cost(
    discharged_energy_kwh: float,
    degradation_cost_per_kwh: float,
) -> float:
    """21.14-21.15, verbatim relationship."""
    return round(discharged_energy_kwh * degradation_cost_per_kwh, 2)


def calculate_net_battery_saving(
    gross_saving: float,
    degradation_cost: float,
) -> float:
    """21.15, verbatim formula."""
    return round(gross_saving - degradation_cost, 2)


def calculate_load_shift_saving(
    energy_kwh: float,
    expensive_price: float,
    cheap_price: float,
) -> float:
    """21.17, verbatim."""
    price_difference = expensive_price - cheap_price

    return round(max(energy_kwh * price_difference, 0), 2)


def calculate_solar_contribution_percent(
    solar_used_kwh: float,
    consumption_kwh: float,
) -> float:
    """21.25, verbatim formula."""
    if consumption_kwh <= 0:
        return 0.0

    return round((solar_used_kwh / consumption_kwh) * 100, 2)


def calculate_grid_dependency_percent(
    grid_import_kwh: float,
    consumption_kwh: float,
) -> float:
    """21.26, verbatim formula."""
    if consumption_kwh <= 0:
        return 0.0

    return round((grid_import_kwh / consumption_kwh) * 100, 2)


def calculate_renewable_coverage_percent(
    solar_used_kwh: float,
    consumption_kwh: float,
) -> float:
    """
    21.27 gives no formula distinct from 21.25's Solar Contribution —
    same "share of consumption met by solar" concept, so this reuses
    that math rather than inventing a second definition.
    """
    return calculate_solar_contribution_percent(solar_used_kwh, consumption_kwh)


def calculate_roi_percent(
    annual_benefit: float,
    initial_investment: float,
) -> float | None:
    """21.28, verbatim formula. None when no investment cost is on file."""
    if not initial_investment or initial_investment <= 0:
        return None

    return round((annual_benefit / initial_investment) * 100, 2)


def calculate_payback_period_years(
    initial_investment: float,
    annual_net_benefit: float,
) -> float | None:
    """21.29, verbatim formula."""
    if not annual_net_benefit or annual_net_benefit <= 0:
        return None
    if not initial_investment or initial_investment <= 0:
        return None

    return round(initial_investment / annual_net_benefit, 2)
