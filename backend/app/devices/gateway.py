from app.devices.factory import create_device_adapter


class DeviceGateway:
    async def read_device(self, device):
        adapter = create_device_adapter(device)

        await adapter.connect()
        data = await adapter.read_data()
        await adapter.disconnect()

        return data
