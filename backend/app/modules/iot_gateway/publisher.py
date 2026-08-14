"""
STEP 39.20: Command Publisher.

Publishes commands to MQTT broker and manages delivery state.
"""

import logging
from datetime import datetime, timezone

from app.modules.iot_gateway.schemas import MQTTCommandMessage
from app.modules.iot_gateway.topics import command_topic

logger = logging.getLogger(__name__)


class CommandPublisher:
    """
    Publishes commands to MQTT.

    In production this connects to the MQTT broker.
    For MVP, commands are logged and the mock device handles them in-process.
    """

    def __init__(self, broker_url: str | None = None):
        self._broker_url = broker_url
        self._connected = False
        self._published: list[dict] = []  # For testing

    async def connect(self) -> bool:
        """Connect to MQTT broker."""
        logger.info(f"CommandPublisher: connecting to {self._broker_url or 'mock'}")
        self._connected = True
        return True

    async def disconnect(self) -> None:
        self._connected = False

    async def publish_command(
        self,
        factory_id: str,
        device_id: str,
        command: MQTTCommandMessage,
    ) -> bool:
        """
        39.20: Publish command to device topic.
        Returns True if published (not necessarily received by device).
        """
        topic = command_topic(factory_id, device_id)
        payload = command.model_dump_json()

        logger.info(
            f"Publishing command {command.command_id} to {topic}",
            extra={
                "command_id": command.command_id,
                "device_id": device_id,
                "trace_id": command.trace_id,
                "topic": topic,
            },
        )

        # In production: await self._mqtt_client.publish(topic, payload, qos=1)
        # For MVP: store for testing
        self._published.append({
            "topic": topic,
            "payload": payload,
            "command_id": command.command_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return True

    @property
    def published_commands(self) -> list[dict]:
        """For testing: list of published commands."""
        return self._published

    def clear_published(self) -> None:
        """For testing: clear published history."""
        self._published.clear()
