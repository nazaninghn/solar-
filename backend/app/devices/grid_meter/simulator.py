import random
from datetime import datetime, timezone

from app.devices.grid_meter.base import BaseGridMeter
from app.devices.scenario import get_scenario

# SUNNY/PEAK_PRICE bias toward one direction (export on a sunny surplus
# day, import when discharging isn't enough to cover a price spike);
# other scenarios keep the original 50/50 coin flip.
_DIRECTION_BIAS = {
    "SUNNY": 0.15,  # mostly export
    "CLOUDY": 0.85,  # mostly import
    "PEAK_PRICE": 0.9,  # mostly import
}


class SimulatorGridMeter(BaseGridMeter):
    """
    A real meter never imports and exports at the same instant — the
    simulator mirrors that by picking one direction per reading rather
    than two independent random values, so its output is internally
    plausible even though it isn't coordinated with the other
    (independently simulated) solar/battery/factory devices. That
    cross-device mismatch is exactly what 26.22's balance validation
    exists to catch, not something this simulator should hide.
    """

    async def connect(self):
        return True

    async def disconnect(self):
        return True

    async def read_data(self):
        if get_scenario() == "DEVICE_OFFLINE":
            raise ConnectionError("Simulated device offline scenario")

        import_probability = _DIRECTION_BIAS.get(get_scenario(), 0.5)

        if random.random() < import_probability:
            import_power = round(random.uniform(0, 1500), 2)
            export_power = 0.0
        else:
            import_power = 0.0
            export_power = round(random.uniform(0, 1500), 2)

        return {
            "import_power_kw": import_power,
            "export_power_kw": export_power,
            "power_kw": import_power - export_power,
            "import_energy_kwh": round(random.uniform(0, 5000), 2),
            "export_energy_kwh": round(random.uniform(0, 3000), 2),
            "voltage": round(random.uniform(395, 405), 1),
            "frequency": round(random.uniform(49.8, 50.2), 2),
            "status": "ONLINE",
            "timestamp": datetime.now(timezone.utc),
        }

    async def get_import_power(self):
        return random.uniform(0, 1500)

    async def get_export_power(self):
        return random.uniform(0, 1500)

    async def get_status(self):
        return "ONLINE"

    async def health_check(self):
        return get_scenario() != "DEVICE_OFFLINE"
