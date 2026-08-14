"""
STEP 32: Energy Action and Command Queue models.

Action represents an approved energy control decision (e.g. discharge battery).
CommandQueue holds individual device commands spawned by an Action.
"""

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


# --- Action Types ---
ACTION_CHARGE_BATTERY = "CHARGE_BATTERY"
ACTION_DISCHARGE_BATTERY = "DISCHARGE_BATTERY"
ACTION_LIMIT_EXPORT = "LIMIT_EXPORT"
ACTION_ENABLE_EXPORT = "ENABLE_EXPORT"
ACTION_SHIFT_LOAD = "SHIFT_LOAD"
ACTION_REDUCE_LOAD = "REDUCE_LOAD"

ALLOWED_ACTION_TYPES = {
    ACTION_CHARGE_BATTERY,
    ACTION_DISCHARGE_BATTERY,
}

# --- Action Statuses ---
STATUS_PENDING = "PENDING"
STATUS_APPROVED = "APPROVED"
STATUS_SCHEDULED = "SCHEDULED"
STATUS_RUNNING = "RUNNING"
STATUS_VERIFYING = "VERIFYING"
STATUS_COMPLETED = "COMPLETED"
STATUS_FAILED = "FAILED"
STATUS_CANCELLED = "CANCELLED"
STATUS_EXPIRED = "EXPIRED"
STATUS_REJECTED = "REJECTED"
STATUS_BLOCKED = "BLOCKED"

# --- Command Statuses ---
CMD_PENDING = "PENDING"
CMD_SENT = "SENT"
CMD_SUCCESS = "SUCCESS"
CMD_FAILED = "FAILED"
CMD_TIMEOUT = "TIMEOUT"


class EnergyAction(Base):
    """32.5: Represents a high-level energy control action."""

    __tablename__ = "energy_actions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recommendation_id: Mapped[int | None] = mapped_column(
        ForeignKey("recommendations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    device_id: Mapped[int | None] = mapped_column(
        ForeignKey("devices.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default=STATUS_PENDING)

    # Scheduling
    scheduled_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scheduled_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Targets
    target_power_kw: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_energy_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_soc: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Users
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Failure
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Extensible metadata (JSON-serializable string)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class CommandQueue(Base):
    """32.13: Individual device commands spawned by an EnergyAction."""

    __tablename__ = "command_queue"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    action_id: Mapped[int] = mapped_column(
        ForeignKey("energy_actions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    command_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default=CMD_PENDING)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # 32.16: Idempotency key
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Error
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
