from datetime import date as date_type
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.query_utils import utc_date
from app.energy.schemas import EnergyInput
from app.energy.service import calculate_energy_state
from app.models.battery_system import BatterySystem
from app.models.energy_daily import EnergyDaily
from app.models.energy_hourly import EnergyHourly
from app.models.energy_reading import EnergyReading
from app.modules.pricing.service import get_current_price


def create_reading(
    db: Session,
    factory_id: int,
    data,
) -> EnergyReading:
    reading = EnergyReading(
        factory_id=factory_id,
        timestamp=data.timestamp,
        solar_generation_kwh=data.solar_generation_kwh,
        consumption_kwh=data.consumption_kwh,
        grid_import_kwh=data.grid_import_kwh,
        grid_export_kwh=data.grid_export_kwh,
        battery_charge_kwh=data.battery_charge_kwh,
        battery_discharge_kwh=data.battery_discharge_kwh,
        battery_soc_percent=data.battery_soc_percent,
    )

    db.add(reading)
    db.commit()
    db.refresh(reading)

    return reading


def get_readings(
    db: Session,
    factory_id: int,
    start: datetime | None = None,
    end: datetime | None = None,
):
    query = (
        select(EnergyReading)
        .where(EnergyReading.factory_id == factory_id)
        .order_by(EnergyReading.timestamp.asc())
    )

    if start:
        query = query.where(EnergyReading.timestamp >= start)

    if end:
        query = query.where(EnergyReading.timestamp <= end)

    return db.scalars(query).all()


def get_current_energy(db: Session, factory_id: int) -> dict:
    """
    17.30's flow: this is the REST endpoint the frontend calls for the
    initial page load, before the Step 15 WebSocket connects. Prefers
    the same live in-memory snapshot the WebSocket broadcasts feed from
    (Step 16's device polling loop) so the two never disagree; falls
    back to the latest raw EnergyReading row for factories that don't
    have devices configured yet.
    """
    from app.jobs.device_jobs import _latest_by_factory

    cached = _latest_by_factory.get(factory_id)

    if cached:
        inverter = cached.get("INVERTER")
        battery = cached.get("BATTERY")
        grid_meter = cached.get("GRID_METER")
        factory_meter = cached.get("FACTORY_METER")

        grid_import_kw = grid_meter["import_power_kw"] if grid_meter else 0.0
        grid_export_kw = grid_meter["export_power_kw"] if grid_meter else 0.0

        return {
            "solar_power_kw": inverter["power_kw"] if inverter else 0.0,
            "factory_load_kw": factory_meter["power_kw"] if factory_meter else 0.0,
            "battery_soc": battery.get("soc_percent", 0.0) if battery else 0.0,
            "battery_power_kw": battery["power_kw"] if battery else 0.0,
            "grid_power_kw": grid_import_kw - grid_export_kw,
            "grid_import_kw": grid_import_kw,
            "grid_export_kw": grid_export_kw,
            "grid_status": "CONNECTED",
            "timestamp": datetime.now(timezone.utc),
        }

    battery = db.scalar(
        select(BatterySystem).where(BatterySystem.factory_id == factory_id)
    )

    latest_reading = db.scalar(
        select(EnergyReading)
        .where(EnergyReading.factory_id == factory_id)
        .order_by(EnergyReading.timestamp.desc())
        .limit(1)
    )

    if not latest_reading:
        return {
            "solar_power_kw": 0.0,
            "factory_load_kw": 0.0,
            "battery_soc": battery.state_of_charge_percent if battery else 0.0,
            "grid_power_kw": 0.0,
            "grid_status": "UNKNOWN",
        }

    return {
        "solar_power_kw": latest_reading.solar_generation_kwh,
        "factory_load_kw": latest_reading.consumption_kwh,
        "battery_soc": (
            battery.state_of_charge_percent
            if battery
            else (latest_reading.battery_soc_percent or 0.0)
        ),
        "grid_power_kw": latest_reading.grid_import_kwh - latest_reading.grid_export_kwh,
        "grid_import_kw": latest_reading.grid_import_kwh,
        "grid_export_kw": latest_reading.grid_export_kwh,
        "grid_status": "CONNECTED",
        "timestamp": latest_reading.timestamp,
    }


def get_energy_history(
    db: Session,
    factory_id: int,
    start: datetime,
    end: datetime,
    resolution: str = "hour",
) -> list[dict]:
    if resolution == "day":
        rows = db.scalars(
            select(EnergyDaily)
            .where(
                EnergyDaily.factory_id == factory_id,
                EnergyDaily.date >= start.date(),
                EnergyDaily.date <= end.date(),
            )
            .order_by(EnergyDaily.date.asc())
        ).all()

        return [
            {
                "timestamp": row.date,
                "solar_kwh": row.solar_kwh,
                "consumption_kwh": row.consumption_kwh,
                "grid_import_kwh": row.grid_import_kwh,
                "grid_export_kwh": row.grid_export_kwh,
                "data_quality": row.data_quality,
            }
            for row in rows
        ]

    if resolution == "hour":
        rows = db.scalars(
            select(EnergyHourly)
            .where(
                EnergyHourly.factory_id == factory_id,
                EnergyHourly.hour >= start,
                EnergyHourly.hour <= end,
            )
            .order_by(EnergyHourly.hour.asc())
        ).all()

        return [
            {
                "timestamp": row.hour,
                "solar_kwh": row.solar_kwh,
                "consumption_kwh": row.consumption_kwh,
                "grid_import_kwh": row.grid_import_kwh,
                "grid_export_kwh": row.grid_export_kwh,
                "data_quality": row.data_quality,
            }
            for row in rows
        ]

    # Fallback: raw readings, for callers that want finer granularity
    # than the hourly/daily aggregate tables provide. 17.3 mentions
    # 1/5-minute resolutions, but 17.11/17.13 only define Hourly/Daily
    # models — this passthrough covers that gap with the existing raw
    # table instead of adding aggregate tables nothing else asked for.
    readings = get_readings(db, factory_id, start=start, end=end)

    return [
        {
            "timestamp": reading.timestamp,
            "solar_kwh": reading.solar_generation_kwh,
            "consumption_kwh": reading.consumption_kwh,
            "grid_import_kwh": reading.grid_import_kwh,
            "grid_export_kwh": reading.grid_export_kwh,
            "data_quality": "COMPLETE",
        }
        for reading in readings
    ]


def get_energy_summary(
    db: Session,
    factory_id: int,
    start_date: date_type,
    end_date: date_type,
) -> dict:
    result = db.execute(
        select(
            func.coalesce(func.sum(EnergyReading.solar_generation_kwh), 0).label(
                "solar_generation_kwh"
            ),
            func.coalesce(func.sum(EnergyReading.consumption_kwh), 0).label(
                "consumption_kwh"
            ),
            func.coalesce(func.sum(EnergyReading.grid_import_kwh), 0).label(
                "grid_import_kwh"
            ),
            func.coalesce(func.sum(EnergyReading.grid_export_kwh), 0).label(
                "grid_export_kwh"
            ),
        ).where(
            EnergyReading.factory_id == factory_id,
            utc_date(EnergyReading.timestamp) >= start_date,
            utc_date(EnergyReading.timestamp) <= end_date,
        )
    ).one()

    solar = result.solar_generation_kwh
    consumption = result.consumption_kwh
    export = result.grid_export_kwh

    # 17.25's exact formulas — its own 17.24 JSON example doesn't
    # actually match them (the two percentages there are swapped/off
    # relative to what 17.25 computes for the same numbers), so this
    # follows the worked formulas, not the example's literal figures.
    solar_coverage_percent = (
        round((solar / consumption) * 100, 2) if consumption > 0 else 0.0
    )
    self_consumption_percent = (
        round(((solar - export) / solar) * 100, 2) if solar > 0 else 0.0
    )

    return {
        "solar_generation_kwh": round(solar, 2),
        "consumption_kwh": round(consumption, 2),
        "grid_import_kwh": round(result.grid_import_kwh, 2),
        "grid_export_kwh": round(export, 2),
        "self_consumption_percent": self_consumption_percent,
        "solar_coverage_percent": solar_coverage_percent,
    }


def get_factory_energy_state(db: Session, factory_id: int) -> dict:
    """
    18.26's GET /energy/state — assembles real EnergyInput from the same
    sources already built in prior steps (Step 17's current-energy
    service, BatterySystem, Step 10's pricing service) and runs it
    through the Step 18 engine.
    """
    current = get_current_energy(db, factory_id)

    battery = db.scalar(
        select(BatterySystem).where(BatterySystem.factory_id == factory_id)
    )

    price = get_current_price(db, factory_id)

    data = EnergyInput(
        solar_power_kw=current["solar_power_kw"],
        factory_load_kw=current["factory_load_kw"],
        battery_soc=battery.state_of_charge_percent if battery else 0.0,
        battery_available_kw=0.0,  # unused directly — service.calculate_energy_state derives it
        battery_capacity_kwh=battery.capacity_kwh if battery else 0.0,
        grid_price_buy=price.buy_price_per_kwh if price else 0.0,
        grid_price_sell=price.sell_price_per_kwh if price else 0.0,
    )

    state = calculate_energy_state(
        data=data,
        battery_min_soc=battery.min_soc_percent if battery else 10.0,
        battery_max_soc=battery.max_soc_percent if battery else 95.0,
        battery_max_charge_kw=(battery.charge_rate_kw or 0.0) if battery else 0.0,
        battery_max_discharge_kw=(battery.discharge_rate_kw or 0.0) if battery else 0.0,
    )

    return {
        "solar": {"power_kw": current["solar_power_kw"]},
        "consumption": {"power_kw": current["factory_load_kw"]},
        "battery": {
            "soc": data.battery_soc,
            "available_discharge_kwh": state["battery"]["available_for_discharge_kwh"],
        },
        "grid": {
            "import_kw": state["balance"]["grid_to_load_kw"],
            "buy_price": data.grid_price_buy,
            "sell_price": data.grid_price_sell,
        },
        "decision": state["decision"],
    }
