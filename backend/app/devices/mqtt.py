from app.devices.base import BaseDevice


class MqttAdapter(BaseDevice):
    """26.5, 26.10: connection_type="MQTT" placeholder — see modbus.py's
    docstring for why this raises rather than connecting to anything."""

    async def connect(self):
        raise NotImplementedError("MQTT connectivity is not implemented yet")

    async def disconnect(self):
        raise NotImplementedError("MQTT connectivity is not implemented yet")

    async def read_data(self):
        raise NotImplementedError("MQTT connectivity is not implemented yet")

    async def health_check(self):
        raise NotImplementedError("MQTT connectivity is not implemented yet")
