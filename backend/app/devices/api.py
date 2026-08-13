from app.devices.base import BaseDevice


class ApiAdapter(BaseDevice):
    """
    26.5, 26.10: connection_type="API" placeholder — a generic adapter
    for devices whose manufacturer exposes their own HTTP API to poll
    (as opposed to Modbus/MQTT, or the device pushing to this backend's
    own telemetry-ingestion endpoint). See modbus.py's docstring for why
    this raises rather than connecting to anything; a real manufacturer
    integration is expected to become its own adapters/<vendor>.py
    (26.32) rather than growing branches inside this generic one.
    """

    async def connect(self):
        raise NotImplementedError("Generic API connectivity is not implemented yet")

    async def disconnect(self):
        raise NotImplementedError("Generic API connectivity is not implemented yet")

    async def read_data(self):
        raise NotImplementedError("Generic API connectivity is not implemented yet")

    async def health_check(self):
        raise NotImplementedError("Generic API connectivity is not implemented yet")
