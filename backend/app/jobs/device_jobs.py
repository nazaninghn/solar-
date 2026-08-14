import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.analytics.calculator import validate_power_reading, validate_soc_reading
from app.database.session import SessionLocal
from app.devices.gateway import DeviceGateway
from app.devices.validation import MAX_PLAUSIBLE_POWER_KW
from app.models.device import Device
from app.models.device_energy_reading import DeviceEnergyReading
from app.realtime.manager import manager

logger = logging.getLogger(__name__)

gateway = DeviceGateway()

# Adapter output keys already captured by their own DeviceEnergyReading
# column — anything else (e.g. a GRID_METER's import_power_kw/
# export_power_kw split, or a manufacturer's mppt_1_voltage) goes into
# raw_data instead, same principle as the telemetry-ingestion endpoint's
# extra="allow" handling.
_KNOWN_TELEMETRY_KEYS = {
    "power_kw", "energy_today_kwh", "voltage", "frequency",
    "soc_percent", "status", "timestamp",
}

# Latest reading per factory, keyed by device_type — needed because a
# WebSocket message (Step 15) is one composite factory-level snapshot,
# but each device poll only produces one device's reading at a time.
# This is the minimal version of the "Energy Service" 16.20's flow
# diagram names but doesn't give code for; 16.25 explicitly scopes
# proper historical storage/aggregation to the next step, so this only
# keeps the latest value per device type in memory.
_latest_by_factory: dict[int, dict[str, dict]] = defaultdict(dict)


def get_active_devices(db) -> list[Device]:
    return db.scalars(select(Device).where(Device.is_active.is_(True))).all()


async def poll_devices() -> None:
    db = SessionLocal()

    try:
        devices = get_active_devices(db)
        touched_factories = set()

        for device in devices:
            try:
                data = await gateway.read_device(device)

                device.status = data.get("status", "ONLINE")
                device.last_seen_at = datetime.now(timezone.utc)
                device.consecutive_error_count = 0
                device.last_error_message = None

                _latest_by_factory[device.factory_id][device.device_type] = data
                touched_factories.add(device.factory_id)

                power_kw = data.get("power_kw")
                soc_percent = data.get("soc_percent")

                # power_kw is NOT NULL on the table — a genuinely absent
                # value (not merely an implausible one) has nothing to
                # persist, so this device is skipped this cycle rather
                # than storing a fabricated 0.0 tagged as data.
                if power_kw is None:
                    continue

                # 22.32/31.19-31.20: still validated before persisting,
                # but a failing reading is now stored as data_quality=
                # INVALID rather than silently dropped — 31.7 wants raw
                # payloads kept for debugging even when the parsed
                # values look wrong. Only INVERTER and FACTORY_METER
                # can't be negative — BATTERY (26.20's charge/discharge
                # sign) and GRID_METER (net import minus export) are
                # legitimately signed.
                data_quality = "GOOD"
                if abs(power_kw) > MAX_PLAUSIBLE_POWER_KW:
                    data_quality = "INVALID"
                elif device.device_type in ("INVERTER", "FACTORY_METER") and not validate_power_reading(power_kw):
                    data_quality = "INVALID"
                elif soc_percent is not None and not validate_soc_reading(soc_percent):
                    data_quality = "INVALID"

                raw_data = {
                    k: v for k, v in data.items() if k not in _KNOWN_TELEMETRY_KEYS
                } or None

                # 26.36: upsert-on-conflict, not a plain insert — the
                # (device_id, timestamp) unique constraint means a raw
                # db.add() could raise on a rare timestamp collision and
                # roll back every other device's reading in this same
                # commit along with it.
                db.execute(
                    insert(DeviceEnergyReading)
                    .values(
                        factory_id=device.factory_id,
                        device_id=device.id,
                        timestamp=data.get(
                            "timestamp", datetime.now(timezone.utc)
                        ),
                        power_kw=power_kw,
                        energy_kwh=data.get("energy_today_kwh"),
                        voltage=data.get("voltage"),
                        frequency=data.get("frequency"),
                        soc_percent=soc_percent,
                        raw_data=raw_data,
                        status=data.get("status", "ONLINE"),
                        data_quality=data_quality,
                    )
                    .on_conflict_do_nothing(
                        index_elements=["device_id", "timestamp"],
                    )
                )
            except Exception as error:
                device.status = "ERROR"
                device.consecutive_error_count += 1
                device.last_error_message = str(error)[:500]
                # WARNING, not ERROR — a single device failing to poll
                # (unsupported connection type, transient timeout) is
                # handled gracefully right here, not a system fault.
                logger.warning(
                    "device %d (%s) poll failed: %s", device.id, device.name, error
                )

        db.commit()

        for factory_id in touched_factories:
            await _broadcast_factory_snapshot(factory_id)
    finally:
        db.close()


async def _broadcast_factory_snapshot(factory_id: int) -> None:
    readings = _latest_by_factory[factory_id]

    inverter = readings.get("INVERTER")
    battery = readings.get("BATTERY")
    grid_meter = readings.get("GRID_METER")
    factory_meter = readings.get("FACTORY_METER")

    solar_power_kw = inverter["power_kw"] if inverter else 0.0
    battery_soc = battery.get("soc_percent", 0.0) if battery else 0.0
    battery_power_kw = battery["power_kw"] if battery else 0.0
    factory_load_kw = factory_meter["power_kw"] if factory_meter else 0.0

    # 26.20's convention for grid: positive = importing, negative =
    # exporting — same "positive is energy flowing into the site" shape
    # as battery's charging convention.
    grid_import_kw = grid_meter["import_power_kw"] if grid_meter else 0.0
    grid_export_kw = grid_meter["export_power_kw"] if grid_meter else 0.0
    grid_power_kw = grid_import_kw - grid_export_kw

    message = {
        "factory_id": factory_id,
        "solar_power_kw": solar_power_kw,
        "factory_load_kw": factory_load_kw,
        "battery_soc": battery_soc,
        "battery_power_kw": battery_power_kw,
        "grid_power_kw": grid_power_kw,
        "grid_import_kw": grid_import_kw,
        "grid_export_kw": grid_export_kw,
        "grid_status": "CONNECTED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    await manager.broadcast(factory_id, message)


async def run_device_polling_loop() -> None:
    """
    25.23's "don't let a job failure take down the worker" applies here
    too, but this loop's 5-second cadence doesn't fit job_runs' shape
    (a JobRun row per tick would be ~17k rows/day for this one loop) —
    logging failures for visibility is the right-sized fix, not trying
    to force a continuous poll loop into the discrete-run tracking model
    the other 6 scheduled jobs use.
    """
    while True:
        try:
            await poll_devices()
        except Exception as error:
            logger.error("poll_devices cycle failed: %s", error)

        await asyncio.sleep(5)
