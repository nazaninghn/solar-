from app.devices.base import BaseDevice


class ModbusAdapter(BaseDevice):
    """
    26.5, 26.10: connection_type="MODBUS" placeholder. The brief is
    explicit that this step doesn't connect to real hardware yet
    ("فعلاً قرار نیست به سخت‌افزار واقعی وصل شویم") — this exists so the
    connection-type roster and file layout match what's asked for, not
    because there's a real Modbus client to wire up. When a real
    Modbus-speaking device shows up, implement connect/read_data/
    health_check against it here; create_device_adapter (app/devices/
    factory.py) is the one place that needs a new branch to dispatch to
    it.
    """

    async def connect(self):
        raise NotImplementedError("Modbus connectivity is not implemented yet")

    async def disconnect(self):
        raise NotImplementedError("Modbus connectivity is not implemented yet")

    async def read_data(self):
        raise NotImplementedError("Modbus connectivity is not implemented yet")

    async def health_check(self):
        raise NotImplementedError("Modbus connectivity is not implemented yet")
