import random
from datetime import datetime, timezone

from app.devices.inverter.base import BaseInverter
from app.devices.scenario import get_scenario

# 26.37's scenario ranges — SUNNY pushes toward this adapter's ceiling,
# CLOUDY toward a heavily-reduced range (cloud cover cutting generation,
# not just "a bit lower"), NORMAL keeps the original Step 16 range.
_POWER_RANGES = {
    "SUNNY": (4000, 4500),
    "CLOUDY": (300, 1200),
}
_DEFAULT_POWER_RANGE = (2500, 4500)


class SimulatorInverter(BaseInverter):
    async def connect(self):
        return True

    async def disconnect(self):
        return True

    async def read_data(self):
        if get_scenario() == "DEVICE_OFFLINE":
            raise ConnectionError("Simulated device offline scenario")

        low, high = _POWER_RANGES.get(get_scenario(), _DEFAULT_POWER_RANGE)
        power = random.uniform(low, high)

        return {
            "power_kw": round(power, 2),
            "energy_today_kwh": 14200,
            "status": "ONLINE",
            "timestamp": datetime.now(timezone.utc),
        }

    async def get_power(self):
        return random.uniform(2500, 4500)

    async def get_energy_today(self):
        return 14200

    async def get_status(self):
        return "ONLINE"

    async def health_check(self):
        return get_scenario() != "DEVICE_OFFLINE"
