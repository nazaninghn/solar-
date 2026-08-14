"""
STEP 41: Observability Models.

Data Quality Events, Source Health, System Metrics snapshots.
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

# Data Quality Status (41.6)
DQ_GOOD = "GOOD"
DQ_DEGRADED = "DEGRADED"
DQ_STALE = "STALE"
DQ_INVALID = "INVALID"
DQ_UNAVAILABLE = "UNAVAILABLE"

# Source Status
SRC_HEALTHY = "HEALTHY"
SRC_DEGRADED = "DEGRADED"
SRC_DOWN = "DOWN"
SRC_UNKNOWN = "UNKNOWN"


class DataQualityEvent(Base):
    """41.13: Quality issue tracking."""

    __tablename__ = "data_quality_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metric: Mapped[str | None] = mapped_column(String(50), nullable=True)
    issue_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM")
    observed_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class DataSource(Base):
    """41.15: External and internal data source health tracking."""

    __tablename__ = "data_sources"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    factory_id: Mapped[int | None] = mapped_column(
        ForeignKey("factories.id", ondelete="CASCADE"), nullable=True, index=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=SRC_UNKNOWN)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    consecutive_failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quality_score: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    last_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SystemMetricSnapshot(Base):
    """41.22: Periodic system metrics snapshot."""

    __tablename__ = "system_metric_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    metric: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    tags_json: Mapped[str | None] = mapped_column(Text, nullable=True)
