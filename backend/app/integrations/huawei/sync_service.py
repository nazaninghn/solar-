"""
Huawei FusionSolar data sync service.

Pulls real-time and recent data from FusionSolar API
and stores it as energy readings in the SolarFlow database.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.integrations.huawei.client import HuaweiFusionSolarClient
from app.models.device import Device
from app.models.energy_reading import EnergyReading

logger = logging.getLogger(__name__)


async def sync_station_data(db: Session, device: Device, config: dict) -> int:
    """
    Sync real-time station data from Huawei FusionSolar.
    Returns the number of readings stored.
    """
    client = HuaweiFusionSolarClient(
        username=config["username"],
        password=config["password"],
        base_url=config["base_url"],
    )

    station_code = config.get("station_code")
    if not station_code:
        # Try to discover station
        stations = await client.get_station_list()
        if not stations:
            logger.warning("FusionSolar sync: No stations found")
            return 0
        station_code = stations[0].get("stationCode")

    # Get real-time station KPIs
    realtime = await client.get_station_realtime(station_code)
    if not realtime:
        logger.warning("FusionSolar sync: No real-time data")
        return 0

    kpis = realtime.get("dataItemMap", {})

    # Map Huawei KPIs to our energy reading model
    now = datetime.now(timezone.utc)
    solar_kw = kpis.get("real_health_state", 0)  # Active power
    day_power = kpis.get("day_power", 0)  # kWh today
    total_power = kpis.get("total_power", 0)  # Total lifetime kWh
    day_income = kpis.get("day_income", 0)  # Revenue today

    # Create energy reading
    reading = EnergyReading(
        factory_id=device.factory_id,
        timestamp=now,
        solar_generation_kwh=float(day_power) if day_power else 0.0,
        consumption_kwh=0.0,  # Needs smart meter data
        grid_import_kwh=0.0,
        grid_export_kwh=0.0,
        battery_charge_kwh=0.0,
        battery_discharge_kwh=0.0,
    )

    db.add(reading)
    device.last_seen_at = now
    device.status = "ONLINE"
    db.commit()

    count = 1

    # Also try to get individual device data for more details
    try:
        devices = await client.get_device_list(station_code)
        for dev in devices:
            dev_type_id = dev.get("devTypeId")
            dev_id = str(dev.get("id", ""))

            if dev_type_id == 1:  # String inverter
                dev_data = await client.get_device_realtime(dev_id, dev_type_id)
                if dev_data:
                    data_map = dev_data.get("dataItemMap", {})
                    active_power = data_map.get("active_power", 0)
                    logger.info(
                        f"FusionSolar inverter {dev.get('devName')}: "
                        f"{active_power} kW active power"
                    )
    except Exception as e:
        logger.warning(f"FusionSolar device detail sync failed: {e}")

    await client.disconnect()

    logger.info(f"FusionSolar sync complete: {count} reading(s) stored")
    return count
