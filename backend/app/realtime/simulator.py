import asyncio
import random
from datetime import datetime, timezone

from app.realtime.manager import manager


async def simulate_factory_energy(factory_id: int) -> None:
    while True:
        solar = random.uniform(2500, 4500)
        load = random.uniform(3500, 5000)

        battery_soc = random.uniform(50, 90)
        battery_power = random.uniform(-800, 800)

        grid_power = load - solar

        message = {
            "factory_id": factory_id,
            "solar_power_kw": round(solar, 2),
            "factory_load_kw": round(load, 2),
            "battery_soc": round(battery_soc, 2),
            "battery_power_kw": round(battery_power, 2),
            "grid_power_kw": round(grid_power, 2),
            "grid_status": "CONNECTED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        await manager.broadcast(factory_id, message)

        await asyncio.sleep(5)
