"""
STEP 52: Disaster Recovery Models.

Recovery Events, DR Drills, Recovery Checklists, RPO/RTO Targets.
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


class RecoveryTarget(Base):
    """52.13: RPO/RTO targets per service."""
    __tablename__ = "recovery_targets"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    service: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    rpo_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    rto_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=120)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="HIGH")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RecoveryDrill(Base):
    """52.43-52.46: DR drill execution records."""
    __tablename__ = "recovery_drills"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    scenario: Mapped[str] = mapped_column(String(100), nullable=False)
    environment: Mapped[str] = mapped_column(String(20), nullable=False, default="staging")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PLANNED")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    detection_time_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    restore_time_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    validation_time_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_recovery_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    data_loss_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    rto_met: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    rpo_met: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    issues_found: Mapped[str | None] = mapped_column(Text, nullable=True)
    executed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RecoveryEvent(Base):
    """52.35: Recovery timeline events during real or drill incidents."""
    __tablename__ = "recovery_events"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    drill_id: Mapped[int | None] = mapped_column(
        ForeignKey("recovery_drills.id", ondelete="CASCADE"), nullable=True, index=True
    )
    incident_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    actor: Mapped[str | None] = mapped_column(String(100), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RecoveryChecklist(Base):
    """52.51: Recovery verification checklist."""
    __tablename__ = "recovery_checklists"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    drill_id: Mapped[int | None] = mapped_column(
        ForeignKey("recovery_drills.id", ondelete="CASCADE"), nullable=True, index=True
    )
    item: Mapped[str] = mapped_column(String(200), nullable=False)
    checked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    checked_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
