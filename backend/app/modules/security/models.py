"""
STEP 47: Security Models.

Security Events, Account Lockout, Backup Records, DR Plan.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class SecurityEvent(Base):
    """47.33: Security event tracking."""
    __tablename__ = "security_events"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM")
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 84: the Step 79 correlation job (every 5 min, now actually
    # populated with real data since Step 82 wired log_security_event
    # into real call sites) does `WHERE created_at >= window_start` over
    # this whole table on every run — needed its own index rather than
    # relying on the individual event_type/user_id/organization_id ones,
    # none of which help a bare time-range scan.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class AccountLockout(Base):
    """47.9: Account lockout tracking."""
    __tablename__ = "account_lockouts"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    failed_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BackupRecord(Base):
    """47.35-47.36: Backup history and verification."""
    __tablename__ = "backup_records"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    backup_type: Mapped[str] = mapped_column(String(20), nullable=False)  # DAILY, WEEKLY, MONTHLY
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    storage_location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    encrypted: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class DisasterRecoveryPlan(Base):
    """47.41: DR plan configuration."""
    __tablename__ = "disaster_recovery_plans"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    scenario: Mapped[str] = mapped_column(String(100), nullable=False)
    rpo_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    rto_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=120)
    runbook: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_tested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    test_result: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
