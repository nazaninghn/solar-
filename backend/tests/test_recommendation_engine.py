from datetime import datetime, timedelta, timezone

from app.models.production_line import ProductionLine
from app.modules.recommendations.engine import (
    EnergyContext,
    TimeWindow,
    generate_recommendations,
)

NOW = datetime.now(timezone.utc)


def _base_context(**overrides) -> EnergyContext:
    defaults = dict(
        battery_soc=50,
        battery_capacity_kwh=5000,
        battery_min_soc=10,
        battery_max_soc=95,
        solar_forecast_kwh=1000,
        expected_consumption_kwh=4000,
        expected_solar_reduction_percent=0,
        current_buy_price=5000,
        current_sell_price=3000,
        price_level="medium",
        high_price_window=None,
        low_price_window=None,
        surplus_window=None,
        flexible_production_lines=[],
    )
    defaults.update(overrides)
    return EnergyContext(**defaults)


def test_cloudy_forecast_high_price_charges_battery():
    """Test 1 (20.34): -35% solar forecast, battery 50%, HIGH grid price -> CHARGE_BATTERY."""
    context = _base_context(
        expected_solar_reduction_percent=35,
        battery_soc=50,
        price_level="high",
        high_price_window=TimeWindow(
            start=NOW + timedelta(hours=6),
            end=NOW + timedelta(hours=10),
            price_per_kwh=8000,
        ),
    )

    types = [r["type"] for r in generate_recommendations(context)]

    assert "CHARGE_BATTERY" in types


def test_solar_surplus_battery_full_sells_to_grid():
    """Test 2 (20.34): solar surplus, battery 95%, HIGH sell price -> SELL_TO_GRID."""
    context = _base_context(
        battery_soc=95,
        battery_max_soc=95,
        current_sell_price=6000,
        surplus_window=TimeWindow(
            start=NOW + timedelta(hours=3),
            end=NOW + timedelta(hours=6),
            amount_kwh=1500,
            price_per_kwh=6000,
        ),
    )

    types = [r["type"] for r in generate_recommendations(context)]

    assert "SELL_TO_GRID" in types


def test_solar_low_battery_available_high_price_discharges():
    """Test 3 (20.34): solar low, battery 85%, HIGH grid price -> DISCHARGE_BATTERY."""
    context = _base_context(
        expected_solar_reduction_percent=40,
        battery_soc=85,
        price_level="high",
        current_buy_price=9000,
    )

    types = [r["type"] for r in generate_recommendations(context)]

    assert "DISCHARGE_BATTERY" in types


def test_solar_low_battery_low_price_low_buys_from_grid():
    """Test 4 (20.34): solar low, battery 10%, LOW grid price -> BUY_FROM_GRID."""
    context = _base_context(
        expected_solar_reduction_percent=40,
        battery_soc=10,
        battery_min_soc=10,
        price_level="low",
        current_buy_price=2000,
        low_price_window=TimeWindow(
            start=NOW + timedelta(hours=1),
            end=NOW + timedelta(hours=4),
            price_per_kwh=2000,
        ),
    )

    types = [r["type"] for r in generate_recommendations(context)]

    assert "BUY_FROM_GRID" in types


def test_flexible_line_high_price_shifts_load():
    """Test 5 (20.34): flexible production line, cheap solar-rich hour available,
    expensive hour ahead -> SHIFT_LOAD."""
    line = ProductionLine(
        id=1,
        factory_id=1,
        name="Production Line 2",
        power_kw=800,
        flexible=True,
        minimum_run_time_hours=4,
        priority="MEDIUM",
        created_at=NOW,
    )

    context = _base_context(
        price_level="high",
        expected_solar_reduction_percent=25,
        current_buy_price=9000,
        current_sell_price=3000,
        flexible_production_lines=[line],
    )

    types = [r["type"] for r in generate_recommendations(context)]

    assert "SHIFT_LOAD" in types
