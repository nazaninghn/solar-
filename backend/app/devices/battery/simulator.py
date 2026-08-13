import random
from datetime import datetime, timezone

from app.devices.battery.base import BaseBattery
from app.devices.scenario import get_scenario

# 26.20's convention, adopted project-wide: positive power_kw means
# charging, negative means discharging.
_POWER_RANGES = {
    "SUNNY": (200, 800),  # surplus solar charges the battery
    "CLOUDY": (-800, -200),  # low solar, battery covers the gap
    "PEAK_PRICE": (-800, -400),  # discharge to avoid buying at peak price
}
_DEFAULT_POWER_RANGE = (-800, 800)

_SOC_RANGES = {
    "BATTERY_LOW": (3, 9),
}
_DEFAULT_SOC_RANGE = (50, 90)


class SimulatorBattery(BaseBattery):
    async def connect(self):
        return True

    async def disconnect(self):
        return True

    async def read_data(self):
        if get_scenario() == "DEVICE_OFFLINE":
            raise ConnectionError("Simulated device offline scenario")

        power_low, power_high = _POWER_RANGES.get(get_scenario(), _DEFAULT_POWER_RANGE)
        soc_low, soc_high = _SOC_RANGES.get(get_scenario(), _DEFAULT_SOC_RANGE)

        power = random.uniform(power_low, power_high)
        soc = random.uniform(soc_low, soc_high)

        return {
            "power_kw": round(power, 2),
            # Not part of the brief's normalized EnergyReading schema
            # (16.6 only defines power_kw/energy_today_kwh/status/source)
            # — kept as an extra key since a battery's defining metric
            # isn't power alone. The gateway passes adapter output
            # through untouched, so this is safe to include.
            "soc_percent": round(soc, 2),
            "energy_today_kwh": None,
            "status": "ONLINE",
            "timestamp": datetime.now(timezone.utc),
        }

    async def get_soc(self):
        return random.uniform(50, 90)

    async def get_power(self):
        return random.uniform(-800, 800)

    async def get_status(self):
        return "ONLINE"

    async def health_check(self):
        return get_scenario() != "DEVICE_OFFLINE"
