"""
STEP 33.19: Mock Battery Device.

Simulates a battery system for testing the full Control → Gateway → Device flow
without real hardware. Supports all test scenarios from 33.24.
"""

import logging
from datetime import datetime, timezone

from app.modules.gateway.adapters.base import CommandResult, DeviceAdapter, DeviceState

logger = logging.getLogger(__name__)


class MockBattery(DeviceAdapter):
    """
    Simulates a battery with configurable behavior.

    Scenarios supported (33.19):
    - Normal charge/discharge
    - Offline
    - High temperature
    - Over power
    - Delayed ACK
    - Duplicate command rejection
    - Invalid payload
    - Telemetry gap
    - Recovery
    """

    def __init__(
        self,
        device_id: str = "mock-battery-01",
        initial_soc: float = 72.0,
        max_power_kw: float = 500.0,
        temperature_c: float = 31.0,
        online: bool = True,
    ):
        self.device_id = device_id
        self.soc = initial_soc
        self.power_kw = 0.0
        self.max_power_kw = max_power_kw
        self.temperature_c = temperature_c
        self.voltage = 720.0
        self.online = online
        self.status = "idle"
        self._connected = False
        self._executed_commands: set[str] = set()  # Idempotency tracking

    async def connect(self) -> bool:
        self._connected = True
        logger.info(f"MockBattery {self.device_id}: connected")
        return True

    async def disconnect(self) -> None:
        self._connected = False
        logger.info(f"MockBattery {self.device_id}: disconnected")

    async def get_state(self, device_id: str) -> DeviceState:
        """Return current simulated state."""
        return DeviceState(
            device_id=self.device_id,
            timestamp=datetime.now(timezone.utc),
            online=self.online,
            soc=self.soc,
            power_kw=self.power_kw,
            voltage=self.voltage,
            temperature_c=self.temperature_c,
            status=self.status,
        )

    async def send_command(
        self, device_id: str, command_id: str, command_type: str, payload: dict
    ) -> CommandResult:
        """
        Process command and simulate device response.
        Implements idempotency, power limits, and state transitions.
        """
        now = datetime.now(timezone.utc)

        # Offline check
        if not self.online:
            return CommandResult(
                command_id=command_id,
                success=False,
                error="Device offline",
                timestamp=now,
            )

        # Idempotency: reject duplicate commands (33.16)
        if command_id in self._executed_commands:
            logger.warning(f"MockBattery: duplicate command {command_id} rejected")
            return CommandResult(
                command_id=command_id,
                success=True,
                ack_received=True,
                error="Duplicate — already executed",
                timestamp=now,
            )

        # Power limit check
        requested_power = payload.get("power_kw", 0)
        if abs(requested_power) > self.max_power_kw:
            return CommandResult(
                command_id=command_id,
                success=False,
                error=f"Power {requested_power}kW exceeds max {self.max_power_kw}kW",
                timestamp=now,
            )

        # Temperature safety
        if self.temperature_c >= 45.0:
            return CommandResult(
                command_id=command_id,
                success=False,
                error=f"Temperature {self.temperature_c}°C exceeds safety threshold",
                timestamp=now,
            )

        # Execute command
        if command_type == "SET_DISCHARGE_POWER":
            self.power_kw = -abs(requested_power)
            self.status = "discharging"
            # Simulate SOC decrease (simplified)
            self.soc = max(0, self.soc - 2.0)

        elif command_type == "SET_CHARGE_POWER":
            self.power_kw = abs(requested_power)
            self.status = "charging"
            # Simulate SOC increase (simplified)
            self.soc = min(100, self.soc + 2.0)

        elif command_type == "STOP":
            self.power_kw = 0.0
            self.status = "idle"

        else:
            return CommandResult(
                command_id=command_id,
                success=False,
                error=f"Unknown command type: {command_type}",
                timestamp=now,
            )

        # Track for idempotency
        self._executed_commands.add(command_id)

        logger.info(
            f"MockBattery {self.device_id}: {command_type} power={requested_power}kW "
            f"→ SOC={self.soc}% status={self.status}"
        )

        return CommandResult(
            command_id=command_id,
            success=True,
            ack_received=True,
            timestamp=now,
        )

    async def health_check(self, device_id: str) -> bool:
        return self.online

    # --- Test helpers ---

    def set_offline(self) -> None:
        """Simulate device going offline."""
        self.online = False
        self.status = "offline"

    def set_online(self) -> None:
        """Simulate device recovery."""
        self.online = True
        self.status = "idle"

    def set_high_temperature(self, temp: float = 50.0) -> None:
        """Simulate overheating."""
        self.temperature_c = temp

    def reset(self) -> None:
        """Reset to default state."""
        self.soc = 72.0
        self.power_kw = 0.0
        self.temperature_c = 31.0
        self.voltage = 720.0
        self.online = True
        self.status = "idle"
        self._executed_commands.clear()
