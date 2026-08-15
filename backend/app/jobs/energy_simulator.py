"""
Energy Data Simulator — generates realistic telemetry every 15 minutes.
Runs as a background job so Dashboard always has fresh data.
"""

import math
import random
import logging
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.session import SessionLocal

logger = logging.getLogger(__name__)


def generate_energy_reading():
    """Generate one realistic energy reading for the current time."""
    now = datetime.now(timezone.utc)
    hour = now.hour

    # Solar (bell curve, peak noon)
    if 6 <= hour <= 20:
        angle = math.pi * (hour - 6) / 14
        solar_kw = 450 * math.sin(angle) * random.uniform(0.7, 1.1)
    else:
        solar_kw = 0

    # Load (high during work, low at night)
    if 8 <= hour <= 17:
        load_kw = random.uniform(350, 550)
    elif 6 <= hour <= 8 or 17 <= hour <= 20:
        load_kw = random.uniform(200, 350)
    else:
        load_kw = random.uniform(80, 150)

    net = solar_kw - load_kw
    grid_import = max(0, -net)
    grid_export = max(0, net * 0.8)
    battery_charge = max(0, net * 0.3) if net > 0 else 0
    battery_discharge = max(0, -net * 0.2) if net < 0 else 0

    return {
        "factory_id": 1,
        "timestamp": now,
        "solar_generation_kwh": round(solar_kw, 2),
        "consumption_kwh": round(load_kw, 2),
        "grid_import_kwh": round(grid_import, 2),
        "grid_export_kwh": round(grid_export, 2),
        "battery_charge_kwh": round(battery_charge, 2),
        "battery_discharge_kwh": round(battery_discharge, 2),
        "source": "simulator",
    }


def run_energy_simulator():
    """Insert one energy reading into the database."""
    try:
        db: Session = SessionLocal()
        reading = generate_energy_reading()

        db.execute(text("""
            INSERT INTO energy_readings (factory_id, timestamp, solar_generation_kwh, consumption_kwh,
                grid_import_kwh, grid_export_kwh, battery_charge_kwh, battery_discharge_kwh, source)
            VALUES (:factory_id, :timestamp, :solar_generation_kwh, :consumption_kwh,
                :grid_import_kwh, :grid_export_kwh, :battery_charge_kwh, :battery_discharge_kwh, :source)
            ON CONFLICT (factory_id, timestamp, source) DO NOTHING
        """), reading)

        db.commit()
        db.close()
        logger.info(f"Simulator: solar={reading['solar_generation_kwh']}kW load={reading['consumption_kwh']}kW")
    except Exception as e:
        logger.error(f"Simulator failed: {e}")
