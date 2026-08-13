import random
from datetime import datetime, timezone

from app.devices.factory_meter.base import BaseFactoryMeter
from app.devices.scenario import get_scenario


class SimulatorFactoryMeter(BaseFactoryMeter):
    async def connect(self):
        return True

    async def disconnect(self):
        return True

    async def read_data(self):
        if get_scenario() == "DEVICE_OFFLINE":
            raise ConnectionError("Simulated device offline scenario")

        consumption = round(random.uniform(2000, 4000), 2)

        return {
            "power_kw": consumption,
            "energy_today_kwh": round(random.uniform(10000, 30000), 2),
            "status": "ONLINE",
            "timestamp": datetime.now(timezone.utc),
        }

    async def get_consumption(self):
        return random.uniform(2000, 4000)

    async def get_status(self):
        return "ONLINE"

    async def health_check(self):
        return get_scenario() != "DEVICE_OFFLINE"
