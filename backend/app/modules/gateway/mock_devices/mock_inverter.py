"""
STEP 33.19: Mock Inverter Device.

Simulates a solar inverter for testing telemetry ingestion and control.
"""

import logging
import random
from datetime import datetime, timezone

from app.modules.gateway.adapters.base import CommandResult, DeviceAdapter, DeviceState

logger = logging.getLogger(__name__)


class MockInverter(DeviceAdapter):
    """
    Simulates a solar inverter.
    Produces power based on time-of-day pattern.
    Supports export limiting commands.
    """

    def __init__(
        self,
        device_id: str = "mock-inverter-01",
        capacity_kw: float = 500.0,
        online: bool = True,
    ):
        self.device_id = device_id
        self.capacity_kw = capacity_kw
        self.online = online
        self.current_power_kw = 0.0
        self.export_limit_kw: float | None = None
        self.voltage = 400.0
        self.frequency_hz = 50.0
        self.temperature_c = 42.0
        self.status = "producing"
        self._connected = False

    async def connect(self) -> bool:
        self._connected = True
        logger.info(f"MockInverter {self.device_id}: connected")
        return True

    async def disconnect(self) -> None:
        self._connected = False

    async def get_state(self, device_id: str) -> DeviceState:
        # Simulate solar production (varies slightly each read)
        if self.online:
            base_power = self.capacity_kw * 0.6  # ~60% of capacity
            noise = random.uniform(-20, 20)
            self.current_power_kw = max(0, base_power + noise)
            if self.export_limit_kw is not None:
                self.current_power_kw = min(self.current_power_kw, self.export_limit_kw)

        return DeviceState(
            device_id=self.device_id,
            timestamp=datetime.now(timezone.utc),
            online=self.online,
            power_kw=self.current_power_kw,
            voltage=self.voltage,
            temperature_c=self.temperature_c,
            status=self.status,
        )

    async def send_command(
        self, device_id: str, command_id: str, command_type: str, payload: dict
    ) -> CommandResult:
        now = datetime.now(timezone.utc)

        if not self.online:
            return CommandResult(
                command_id=command_id, success=False, error="Device offline", timestamp=now
            )

        if command_type == "SET_EXPORT_LIMIT":
            limit = payload.get("limit_kw")
            if limit is not None and limit >= 0:
                self.export_limit_kw = limit
                logger.info(f"MockInverter: export limit set to {limit}kW")
                return CommandResult(command_id=command_id, success=True, ack_received=True, timestamp=now)
            return CommandResult(command_id=command_id, success=False, error="Invalid limit", timestamp=now)

        elif command_type == "REMOVE_EXPORT_LIMIT":
            self.export_limit_kw = None
            return CommandResult(command_id=command_id, success=True, ack_received=True, timestamp=now)

        return CommandResult(
            command_id=command_id, success=False, error=f"Unknown command: {command_type}", timestamp=now
        )

    async def health_check(self, device_id: str) -> bool:
        return self.online

    def set_offline(self) -> None:
        self.online = False
        self.status = "offline"
        self.current_power_kw = 0.0

    def set_online(self) -> None:
        self.online = True
        self.status = "producing"
