from app.energy.decision import EnergyAction, decide_energy_action


def test_solar_exceeds_load_battery_available_charges():
    """Test 1 (18.28): Solar > Load, battery has room -> CHARGE_BATTERY."""
    result = decide_energy_action(
        solar_power_kw=5000,
        factory_load_kw=4000,
        battery_soc=50,
        battery_min_soc=10,
        battery_max_soc=95,
        grid_buy_price=8000,
        grid_sell_price=5000,
    )

    assert result["action"] == EnergyAction.CHARGE_BATTERY
    assert result["amount_kw"] == 1000


def test_solar_exceeds_load_battery_full_sells_to_grid():
    """Test 2 (18.28): Solar > Load, battery full -> SELL_TO_GRID."""
    result = decide_energy_action(
        solar_power_kw=5000,
        factory_load_kw=4000,
        battery_soc=95,
        battery_min_soc=10,
        battery_max_soc=95,
        grid_buy_price=8000,
        grid_sell_price=5000,
    )

    assert result["action"] == EnergyAction.SELL_TO_GRID
    assert result["amount_kw"] == 1000


def test_solar_below_load_battery_available_discharges():
    """Test 3 (18.28): Solar < Load, battery has charge -> DISCHARGE_BATTERY."""
    result = decide_energy_action(
        solar_power_kw=2500,
        factory_load_kw=4000,
        battery_soc=50,
        battery_min_soc=10,
        battery_max_soc=95,
        grid_buy_price=8000,
        grid_sell_price=5000,
    )

    assert result["action"] == EnergyAction.DISCHARGE_BATTERY
    assert result["amount_kw"] == 1500


def test_solar_below_load_battery_empty_buys_from_grid():
    """Test 4 (18.28): Solar < Load, battery empty -> BUY_FROM_GRID."""
    result = decide_energy_action(
        solar_power_kw=2500,
        factory_load_kw=4000,
        battery_soc=10,
        battery_min_soc=10,
        battery_max_soc=95,
        grid_buy_price=8000,
        grid_sell_price=5000,
    )

    assert result["action"] == EnergyAction.BUY_FROM_GRID
    assert result["amount_kw"] == 1500


def test_battery_at_min_soc_does_not_discharge():
    """
    Test 5 (18.28): SOC (5%) below min_soc (10%) -> must never discharge,
    even though solar < load. Falls through to BUY_FROM_GRID instead —
    this is the reserve-protection guarantee 18.11 is about.
    """
    result = decide_energy_action(
        solar_power_kw=2500,
        factory_load_kw=4000,
        battery_soc=5,
        battery_min_soc=10,
        battery_max_soc=95,
        grid_buy_price=8000,
        grid_sell_price=5000,
    )

    assert result["action"] != EnergyAction.DISCHARGE_BATTERY
    assert result["action"] == EnergyAction.BUY_FROM_GRID
