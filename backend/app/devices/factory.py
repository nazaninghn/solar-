from app.devices.battery.simulator import SimulatorBattery
from app.devices.factory_meter.simulator import SimulatorFactoryMeter
from app.devices.grid_meter.simulator import SimulatorGridMeter
from app.devices.inverter.simulator import SimulatorInverter


def create_device_adapter(device):
    if device.connection_type == "SIMULATOR":
        if device.device_type == "INVERTER":
            return SimulatorInverter()

        if device.device_type == "BATTERY":
            return SimulatorBattery()

        if device.device_type == "GRID_METER":
            return SimulatorGridMeter()

        if device.device_type == "FACTORY_METER":
            return SimulatorFactoryMeter()

    raise ValueError("Unsupported device")
