from datetime import datetime

from pydantic import BaseModel


class DeviceEnergyReading(BaseModel):
    """
    Named DeviceEnergyReading rather than the brief's plain "EnergyReading"
    (16.6) — that name is already taken by the SQLAlchemy model in
    app/models/energy_reading.py (Step 7), which is a completely
    different shape (factory-level solar/consumption/grid/battery
    columns vs. this per-device power/energy/status normalized reading).
    Reusing the name would make every import in this module ambiguous
    with the DB model.
    """

    device_id: int

    timestamp: datetime

    power_kw: float

    energy_today_kwh: float | None = None

    status: str

    source: str
