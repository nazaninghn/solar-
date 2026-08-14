"""
STEP 38: Production Control Center Models.

Command, CommandVerification, CommandAudit, ControlSnapshot, ControlLock.
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
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base

# Command Types (38.5)
CMD_SET_CHARGE_LIMIT = "SET_BATTERY_CHARGE_LIMIT"
CMD_SET_DISCHARGE_LIMIT = "SET_BATTERY_DISCHARGE_LIMIT"
CMD_START_CHARGE = "START_CHARGE"
CMD_STOP_CHARGE = "STOP_CHARGE"
CMD_START_DISCHARGE = "START_DISCHARGE"
CMD_STOP_DISCHARGE = "STOP_DISCHARGE"
CMD_SET_LOAD_SCHEDULE = "SET_LOAD_SCHEDULE"
CMD_ENABLE_EXPORT = "ENABLE_EXPORT"
CMD_DISABLE_EXPORT = "DISABLE_EXPORT"
CMD_EMERGENCY_STOP = "EMERGENCY_STOP"

# Command Status (38.6)
CS_DRAFT = "DRAFT"
CS_PENDING = "PENDING_APPROVAL"
CS_APPROVED = "APPROVED"
CS_QUEUED = "QUEUED"
CS_SENT = "SENT"
CS_ACKNOWLEDGED = "ACKNOWLEDGED"
CS_EXECUTING = "EXECUTING"
CS_VERIFIED = "VERIFIED"
CS_COMPLETED = "COMPLETED"
CS_FAILED = "FAILED"
CS_CANCELLED = "CANCELLED"
CS_EXPIRED = "EXPIRED"
CS_REJECTED = "REJECTED"

# Priority (38.16)
PRI_SAFETY = "SAFETY"
PRI_HIGH = "HIGH"
PRI_MEDIUM = "MEDIUM"
PRI_LOW = "LOW"

# Verification Status (38.22)
VS_VERIFIED = "VERIFIED"
VS_TIMEOUT = "TIMEOUT"
VS_MISMATCH = "MISMATCH"
VS_NO_TELEMETRY = "NO_TELEMETRY"
VS_DEVICE_REJECTED = "DEVICE_REJECTED"

# Failure Classification (38.41)
FAIL_VALIDATION = "VALIDATION_ERROR"
FAIL_PERMISSION = "PERMISSION_DENIED"
FAIL_SAFETY = "SAFETY_BLOCKED"
FAIL_OFFLINE = "DEVICE_OFFLINE"
FAIL_GATEWAY_TIMEOUT = "GATEWAY_TIMEOUT"
FAIL_DEVICE_REJECTED = "DEVICE_REJECTED"
FAIL_ACK_TIMEOUT = "ACK_TIMEOUT"
FAIL_VERIFY_TIMEOUT = "VERIFICATION_TIMEOUT"
FAIL_MISMATCH = "TELEMETRY_MISMATCH"
FAIL_EXPIRED = "EXPIRED"


class Command(Base):
    """38.4: Production command model."""

    __tablename__ = "commands"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recommendation_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default=CS_DRAFT)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default=PRI_MEDIUM)
    failure_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Timing
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Users
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Idempotency (38.17)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    # Trace (38.40)
    trace_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Retry (38.18)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Rollback (38.23)
    rollback_payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_rollback: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class CommandVerification(Base):
    """38.21: Telemetry-based verification of command execution."""

    __tablename__ = "command_verifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    command_id: Mapped[int] = mapped_column(
        ForeignKey("commands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metric: Mapped[str] = mapped_column(String(50), nullable=False)
    expected_value: Mapped[float] = mapped_column(Float, nullable=False)
    actual_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    tolerance: Mapped[float] = mapped_column(Float, nullable=False, default=0.1)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=VS_VERIFIED)
    evidence_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CommandAudit(Base):
    """38.31: Audit trail for every command state change."""

    __tablename__ = "command_audit"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    command_id: Mapped[int] = mapped_column(
        ForeignKey("commands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="SYSTEM")
    old_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    new_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ControlSnapshot(Base):
    """38.43: System state snapshot at time of command execution."""

    __tablename__ = "control_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    command_id: Mapped[int] = mapped_column(
        ForeignKey("commands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    battery_soc: Mapped[float | None] = mapped_column(Float, nullable=True)
    solar_power_kw: Mapped[float | None] = mapped_column(Float, nullable=True)
    load_power_kw: Mapped[float | None] = mapped_column(Float, nullable=True)
    grid_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    device_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    forecast_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    safety_policy_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    snapshot_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ControlLock(Base):
    """38.26: Device-level lock to prevent concurrent commands."""

    __tablename__ = "control_locks"
    __table_args__ = (
        UniqueConstraint("device_id", "is_active", name="uq_active_device_lock"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    command_id: Mapped[int] = mapped_column(
        ForeignKey("commands.id", ondelete="CASCADE"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
