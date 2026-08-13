from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.battery_system import BatterySystem
from app.models.energy_reading import EnergyReading
from app.models.factory import Factory
from app.modules.battery.strategy import (
    calculate_confidence,
    decide_battery_action,
    explain_battery_action,
)
from app.modules.forecast.service import count_historical_days, get_factory_forecast
from app.modules.pricing.service import get_current_price


def to_response(battery: BatterySystem) -> dict:
    """
    Maps the existing BatterySystem columns (Step 4) onto the field names
    Step 9's API contract expects (soc_percent, health_percent, etc.),
    since we're reusing that table instead of adding a duplicate one.
    """
    return {
        "id": battery.id,
        "factory_id": battery.factory_id,
        "capacity_kwh": battery.capacity_kwh,
        "usable_capacity_kwh": battery.usable_capacity_kwh,
        "soc_percent": battery.state_of_charge_percent,
        "health_percent": battery.state_of_health_percent,
        "cycle_count": battery.cycle_count,
        "max_charge_power_kw": battery.charge_rate_kw,
        "max_discharge_power_kw": battery.discharge_rate_kw,
        "updated_at": battery.updated_at,
    }


def create_battery(db: Session, factory_id: int, data) -> dict:
    existing = db.scalar(
        select(BatterySystem).where(BatterySystem.factory_id == factory_id)
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Battery already exists",
        )

    battery = BatterySystem(
        factory_id=factory_id,
        capacity_kwh=data.capacity_kwh,
        usable_capacity_kwh=data.usable_capacity_kwh,
        state_of_charge_percent=data.soc_percent,
        state_of_health_percent=data.health_percent,
        cycle_count=data.cycle_count,
        charge_rate_kw=data.max_charge_power_kw,
        discharge_rate_kw=data.max_discharge_power_kw,
    )

    db.add(battery)
    db.commit()
    db.refresh(battery)

    return to_response(battery)


def get_battery(db: Session, factory_id: int) -> dict:
    battery = db.scalar(
        select(BatterySystem).where(BatterySystem.factory_id == factory_id)
    )

    if not battery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Battery not configured",
        )

    return to_response(battery)


def _get_latest_solar_surplus_kwh(db: Session, factory_id: int) -> float:
    latest = db.scalar(
        select(EnergyReading)
        .where(EnergyReading.factory_id == factory_id)
        .order_by(EnergyReading.timestamp.desc())
        .limit(1)
    )

    if latest is None:
        return 0.0

    return max(0.0, latest.solar_generation_kwh - latest.consumption_kwh)


async def get_battery_recommendation(db: Session, factory: Factory) -> dict:
    battery = db.scalar(
        select(BatterySystem).where(BatterySystem.factory_id == factory.id)
    )

    if not battery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Battery not configured",
        )

    soc_percent = battery.state_of_charge_percent or 0.0
    solar_surplus_kwh = _get_latest_solar_surplus_kwh(db, factory.id)

    # Step 10 added the Pricing Engine; use the most recent stored price
    # if one exists. Falls back to "unknown" (no-op for both price
    # branches) when the factory has no price data yet.
    current_price = get_current_price(db, factory.id)
    grid_price_level = current_price.price_level if current_price else "unknown"

    try:
        forecast = await get_factory_forecast(db, factory)
        expected_solar_reduction_percent = forecast["solar"]["reduction_percent"]
        weather_confidence = 90.0
    except HTTPException:
        expected_solar_reduction_percent = 0.0
        weather_confidence = 50.0

    historical_data_quality = min(
        100.0, (count_historical_days(db, factory.id) / 7) * 100
    )

    confidence = calculate_confidence(weather_confidence, historical_data_quality)

    action = decide_battery_action(
        soc_percent=soc_percent,
        solar_surplus_kwh=solar_surplus_kwh,
        grid_price_level=grid_price_level,
        expected_solar_reduction_percent=expected_solar_reduction_percent,
    )

    reason = explain_battery_action(
        action=action,
        soc_percent=soc_percent,
        solar_surplus_kwh=solar_surplus_kwh,
        grid_price_level=grid_price_level,
        expected_solar_reduction_percent=expected_solar_reduction_percent,
    )

    target_soc_percent = {
        "charge": 85.0,
        "discharge": 30.0,
        "hold": round(soc_percent, 2),
    }[action.value]

    return {
        "action": action,
        "target_soc_percent": target_soc_percent,
        "reason": reason,
        "confidence": confidence,
    }
