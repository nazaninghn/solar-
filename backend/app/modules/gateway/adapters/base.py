"""
STEP 33.5: Device Adapter Interface.

Business logic talks ONLY to this interface.
Protocol details (MQTT, HTTP, Modbus) stay inside concrete adapters.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DeviceState:
    """Standardized device state returned by any adapter."""

    device_id: str
    timestamp: datetime
    online: bool
    soc: float | None = None
    power_kw: float | None = None
    voltage: float | None = None
    temperature_c: float | None = None
    status: str | None = None
    raw: dict | None = None  # Protocol-specific raw data


@dataclass
class CommandResult:
    """Result of sending a command to a device."""

    command_id: str
    success: bool
    ack_received: bool = False
    error: str | None = None
    timestamp: datetime | None = None


class DeviceAdapter(ABC):
    """
    33.5: Abstract interface for all device adapters.

    Subclasses implement protocol-specific logic:
    - MQTTAdapter
    - HTTPAdapter
    - ModbusAdapter
    - MockAdapter (for testing)
    """

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to device/broker."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Cleanly disconnect."""
        ...

    @abstractmethod
    async def get_state(self, device_id: str) -> DeviceState:
        """Read current state from device."""
        ...

    @abstractmethod
    async def send_command(
        self, device_id: str, command_id: str, command_type: str, payload: dict
    ) -> CommandResult:
        """Send a command and wait for ACK (with timeout)."""
        ...

    @abstractmethod
    async def health_check(self, device_id: str) -> bool:
        """Check if device is reachable and responsive."""
        ...
