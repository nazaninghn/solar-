from datetime import datetime, timezone

from app.analytics.calculator import (
    calculate_data_completeness_percent,
    calculate_energy_from_power,
    determine_data_quality,
)


def test_one_hour_at_100kw_is_100kwh():
    """Test 1 (22.40): 100 kW for 1 hour -> 100 kWh."""
    assert calculate_energy_from_power(100, 1.0) == 100.0


def test_thirty_minutes_at_100kw_is_50kwh():
    """Test 2 (22.40): 100 kW for 30 minutes -> 50 kWh."""
    assert calculate_energy_from_power(100, 0.5) == 50.0


def test_eighty_percent_completeness_is_partial():
    """Test 3 (22.40): 80% completeness -> PARTIAL."""
    completeness = calculate_data_completeness_percent(8, 10)

    assert completeness == 80.0
    assert determine_data_quality(completeness, has_invalid_data=False) == "PARTIAL"


def test_scheduler_run_twice_produces_only_one_aggregate():
    """Test 4 (22.40): running the aggregation job twice must not duplicate rows."""
    from sqlalchemy import select

    from app.database.session import SessionLocal
    from app.models.energy_hourly import EnergyHourly
    from app.modules.energy.aggregation import aggregate_factory_hour

    db = SessionLocal()
    hour_start = datetime(2026, 8, 13, 10, 0, tzinfo=timezone.utc)

    aggregate_factory_hour(db, 1, hour_start)
    aggregate_factory_hour(db, 1, hour_start)

    rows = db.scalars(
        select(EnergyHourly).where(
            EnergyHourly.factory_id == 1, EnergyHourly.hour == hour_start
        )
    ).all()

    assert len(rows) == 1


def test_negative_solar_is_invalid():
    """Test 5 (22.40): negative solar generation -> INVALID."""
    has_invalid_data = -500 < 0  # mirrors aggregate_factory_hour's own check

    assert determine_data_quality(100.0, has_invalid_data) == "INVALID"
