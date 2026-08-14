"""
STEP 39: IoT Gateway Models.

Gateway Registry, Processed Messages (dedup), Dead Letter Queue.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base

# Gateway Status
GW_PROVISIONING = "PROVISIONING"
GW_ONLINE = "ONLINE"
GW_DEGRADED = "DEGRADED"
GW_OFFLINE = "OFFLINE"
GW_DISABLED = "DISABLED"


class Gateway(Base):
    """39.3/39.25: Physical gateway device at factory site."""

    __tablename__ = "gateways"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    gateway_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    serial_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=GW_PROVISIONING)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Health
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    uptime_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    connected_devices: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    signal_quality: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Config (39.47)
    heartbeat_interval_sec: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    offline_threshold_sec: Mapped[int] = mapped_column(Integer, nullable=False, default=300)
    buffer_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=10000)
    telemetry_batch_size: Mapped[int] = mapped_column(Integer, nullable=False, default=50)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ProcessedMessage(Base):
    """39.14: Deduplication tracking for MQTT messages."""

    __tablename__ = "processed_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    message_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    result: Mapped[str] = mapped_column(String(20), nullable=False, default="PROCESSED")


class DeadLetterQueue(Base):
    """39.23: Failed messages for review and controlled replay."""

    __tablename__ = "dead_letter_queue"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    device_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    factory_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    error_code: Mapped[str] = mapped_column(String(50), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
