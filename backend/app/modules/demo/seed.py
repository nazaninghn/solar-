"""
Demo site seeding: a factory with synthetic devices and telemetry.

The demo writes only what real hardware would write — DeviceEnergyReading
rows for push-type ("API") devices — then runs the *production*
aggregation (sync_device_readings_to_energy_reading -> aggregate_factory_hour
-> aggregate_factory_day) to build hourly/daily history. So when a real
factory is connected, its devices push telemetry into the same table and
every downstream feature (analytics, failure prediction, PTF sell offers)
already works on it; nothing here needs to be ported.

Synthetic devices are marked `manufacturer="SYNTHETIC"` and every reading
carries raw_data.source == "SYNTHETIC", so demo data is always
identifiable and removable (purge / --reset).
"""

import logging
from datetime import datetime, timedelta, timezone

import pandas as pd
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.battery_system import BatterySystem
from app.models.device import Device
from app.models.device_energy_reading import DeviceEnergyReading
from app.models.energy_meter import EnergyMeter
from app.models.factory import Factory
from app.models.solar_forecast import SolarForecast
from app.models.solar_system import SolarSystem
from app.models.user import User
from app.modules.demo.synthetic import SYNTHETIC_MARKER, SiteSpec, hourly_pv_forecast, simulate
from app.modules.energy.aggregation import (
    aggregate_factory_day,
    aggregate_factory_hour,
    sync_device_readings_to_energy_reading,
)

logger = logging.getLogger(__name__)

DEMO_FACTORY_NAME = "SolarFlow Demo Factory"
# Minute resolution where the failure model needs it (it reads the last
# few hours at 1-min), 5-min for older history — the aggregator
# integrates power over time, so resolution doesn't bias the energy.
FINE_WINDOW = timedelta(hours=36)
INSERT_BATCH = 5000

_DEVICE_TYPES = {"battery": "BATTERY", "factory_meter": "FACTORY_METER", "grid_meter": "GRID_METER"}
_DEVICE_NAMES = {"battery": "Battery Storage", "factory_meter": "Factory Meter", "grid_meter": "Grid Meter"}


def spec_for(db: Session, factory: Factory) -> SiteSpec:
    """The site spec with soiling anchored to the demo's first reading,
    so live extension continues the same degradation curve instead of
    restarting it at every run."""
    first = db.scalar(
        select(DeviceEnergyReading.timestamp)
        .where(DeviceEnergyReading.factory_id == factory.id)
        .order_by(DeviceEnergyReading.timestamp.asc())
        .limit(1)
    )
    return SiteSpec(soiling_start=pd.Timestamp(first) if first else None)


def get_demo_factory(db: Session) -> Factory | None:
    return db.scalar(
        select(Factory)
        .join(Device, Device.factory_id == Factory.id)
        .where(Device.manufacturer == SYNTHETIC_MARKER, Factory.name == DEMO_FACTORY_NAME)
        .limit(1)
    )


def create_demo_site(db: Session, owner: User, spec: SiteSpec) -> Factory:
    now = datetime.now(timezone.utc)
    total_kw = sum(i.rated_kw for i in spec.inverters)
    factory = Factory(
        organization_id=owner.organization_id,
        name=DEMO_FACTORY_NAME,
        address="Konya Organize Sanayi Bölgesi (synthetic demo site)",
        latitude=spec.latitude,
        longitude=spec.longitude,
        industry="Manufacturing",
        currency="TRY",
        solar_capacity_kw=total_kw,
        battery_capacity_kwh=spec.battery.capacity_kwh,
        timezone=spec.timezone,
        created_at=now,
        updated_at=now,
    )
    db.add(factory)
    db.flush()

    db.add(SolarSystem(
        factory_id=factory.id, installed_capacity_kw=total_kw, panel_count=int(total_kw * 1000 / 550),
        inverter_brand="Synthetic", efficiency_percent=21.0, status="ACTIVE",
        created_at=now, updated_at=now,
    ))
    b = spec.battery
    db.add(BatterySystem(
        factory_id=factory.id, capacity_kwh=b.capacity_kwh,
        usable_capacity_kwh=b.capacity_kwh * (b.max_soc - b.min_soc) / 100,
        state_of_health_percent=94.0, temperature_c=26.0, cycle_count=610,
        charge_rate_kw=b.power_kw, discharge_rate_kw=b.power_kw,
        min_soc_percent=b.min_soc, max_soc_percent=b.max_soc,
        efficiency_percent=b.round_trip_eff * 100, status="IDLE",
        created_at=now, updated_at=now,
    ))

    for inv in spec.inverters:
        db.add(_device(factory.id, inv.name, "INVERTER", inv.key, now))
    for key, dtype in _DEVICE_TYPES.items():
        db.add(_device(factory.id, _DEVICE_NAMES[key], dtype, key, now))
    db.commit()
    db.refresh(factory)
    return factory


def _device(factory_id: int, name: str, device_type: str, key: str, now: datetime) -> Device:
    return Device(
        factory_id=factory_id,
        name=name,
        device_type=device_type,
        manufacturer=SYNTHETIC_MARKER,
        model="demo-site-v1",
        serial_number=f"SYN-{key}",
        # Push-type, like a real logger posting to /telemetry: the poll
        # loop leaves API devices alone.
        connection_type="API",
        status="ONLINE",
        is_active=True,
        created_at=now,
    )


def _devices_by_key(db: Session, factory: Factory) -> dict[str, Device]:
    devices = db.scalars(
        select(Device).where(Device.factory_id == factory.id, Device.manufacturer == SYNTHETIC_MARKER)
    ).all()
    return {d.serial_number.removeprefix("SYN-"): d for d in devices}


def write_readings(db: Session, factory: Factory, spec: SiteSpec, start: datetime, end: datetime) -> int:
    """Synthetic samples for [start, end), coarse then fine resolution."""
    devices = _devices_by_key(db, factory)
    fine_from = max(start, end - FINE_WINDOW)
    windows = [(start, fine_from, "5min"), (fine_from, end, "1min")]

    rows: list[dict] = []
    for w_start, w_end, step in windows:
        if w_end <= w_start:
            continue
        frames = simulate(spec, pd.Timestamp(w_start), pd.Timestamp(w_end), step)
        for key, frame in frames.items():
            device = devices.get(key)
            if device is None:
                continue
            for rec in frame.to_dict("records"):
                rows.append({
                    "factory_id": factory.id,
                    "device_id": device.id,
                    "timestamp": rec["timestamp"].to_pydatetime(),
                    "power_kw": float(rec["power_kw"]),
                    "voltage": _num(rec["voltage"]),
                    "current": _num(rec["current"]),
                    "frequency": _num(rec["frequency"]),
                    "temperature_c": _num(rec["temperature_c"]),
                    "soc_percent": _num(rec["soc_percent"]),
                    "raw_data": rec["raw_data"],
                    "status": "ONLINE",
                    "data_quality": "GOOD",
                })

    for i in range(0, len(rows), INSERT_BATCH):
        db.execute(
            insert(DeviceEnergyReading)
            .values(rows[i : i + INSERT_BATCH])
            .on_conflict_do_nothing(index_elements=["device_id", "timestamp"])
        )
    for device in devices.values():
        device.status = "ONLINE"
        device.last_seen_at = end
        device.consecutive_error_count = 0
    db.commit()
    return len(rows)


def _num(value) -> float | None:
    return None if value is None or pd.isna(value) else float(value)


def aggregate(db: Session, factory: Factory, start: datetime, end: datetime) -> int:
    """Run the production hourly + daily aggregation over completed hours."""
    hour = start.replace(minute=0, second=0, microsecond=0)
    last_complete = end.replace(minute=0, second=0, microsecond=0)
    n = 0
    while hour < last_complete:
        sync_device_readings_to_energy_reading(db, factory.id, hour)
        aggregate_factory_hour(db, factory.id, hour)
        hour += timedelta(hours=1)
        n += 1
    day = start.date()
    while day < end.date():
        aggregate_factory_day(db, factory.id, day)
        day += timedelta(days=1)
    return n


async def ensure_solar_forecast(db: Session, factory: Factory, spec: SiteSpec) -> str:
    """Tomorrow's PV forecast: the real weather-driven production job
    (Open-Meteo for the site's coordinates) when reachable, else the
    synthetic clear-sky estimate. Returns which one was used."""
    try:
        from app.forecast.service import generate_and_store_solar_forecast

        await generate_and_store_solar_forecast(db, factory, days=3)
        return "open-meteo"
    except Exception as error:
        db.rollback()
        logger.warning("Real solar forecast unavailable (%s); using synthetic", error)

    start = pd.Timestamp.now(tz="UTC").normalize()
    forecast = hourly_pv_forecast(spec, start, hours=72)
    now = datetime.now(timezone.utc)
    for ts, row in forecast.iterrows():
        stmt = insert(SolarForecast).values(
            factory_id=factory.id, timestamp=ts.to_pydatetime(),
            expected_power_kw=float(row["expected_power_kw"]),
            expected_energy_kwh=float(row["expected_energy_kwh"]),
            confidence=0.6, is_stale=False, created_at=now,
        )
        db.execute(stmt.on_conflict_do_nothing())
    db.commit()
    return "synthetic"


def latest_reading_at(db: Session, factory: Factory) -> datetime | None:
    return db.scalar(
        select(DeviceEnergyReading.timestamp)
        .where(DeviceEnergyReading.factory_id == factory.id)
        .order_by(DeviceEnergyReading.timestamp.desc())
        .limit(1)
    )


def extend_to_now(db: Session, factory: Factory, spec: SiteSpec) -> int:
    """Append synthetic telemetry from the last reading up to now — what
    the demo feeder job calls, standing in for devices pushing live."""
    last = latest_reading_at(db, factory)
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    if last is None or now - last < timedelta(minutes=1):
        return 0
    return write_readings(db, factory, spec, last + timedelta(minutes=1), now)


def purge(db: Session, factory: Factory) -> None:
    """Delete the demo factory (cascades devices, readings, history,
    forecasts, offers, assessments). Only ever a factory whose devices
    are SYNTHETIC — never real data."""
    if not _devices_by_key(db, factory):
        raise ValueError("Refusing to purge: factory has no synthetic devices")
    # These three reference factories with NO ACTION instead of CASCADE
    # (older migrations), so they must go first; everything else —
    # devices and all device-scoped tables — cascades from the factory.
    for model in (BatterySystem, SolarSystem, EnergyMeter):
        db.execute(delete(model).where(model.factory_id == factory.id))
    db.execute(delete(Factory).where(Factory.id == factory.id))
    db.commit()
