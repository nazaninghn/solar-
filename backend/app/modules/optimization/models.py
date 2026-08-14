"""
STEP 36: Optimization Engine Models.

Smart Recommendations, Flexible Loads, Recommendation History, Optimization Snapshots.
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

# Recommendation Types (36.3)
REC_CHARGE_BATTERY = "CHARGE_BATTERY"
REC_DISCHARGE_BATTERY = "DISCHARGE_BATTERY"
REC_BUY_GRID = "BUY_GRID_POWER"
REC_SELL_SURPLUS = "SELL_SURPLUS"
REC_SHIFT_LOAD = "SHIFT_LOAD"
REC_REDUCE_LOAD = "REDUCE_LOAD"
REC_WAIT = "WAIT"
REC_NO_ACTION = "NO_ACTION"

# Status (36.7)
REC_DRAFT = "DRAFT"
REC_PENDING = "PENDING_APPROVAL"
REC_APPROVED = "APPROVED"
REC_REJECTED = "REJECTED"
REC_SCHEDULED = "SCHEDULED"
REC_EXECUTING = "EXECUTING"
REC_COMPLETED = "COMPLETED"
REC_EXPIRED = "EXPIRED"
REC_CANCELLED = "CANCELLED"
REC_FAILED = "FAILED"

# Priority (36.8)
PRIORITY_LOW = "LOW"
PRIORITY_MEDIUM = "MEDIUM"
PRIORITY_HIGH = "HIGH"
PRIORITY_CRITICAL = "CRITICAL"


class SmartRecommendation(Base):
    """36.6: Enhanced recommendation with explainability and scoring."""

    __tablename__ = "smart_recommendations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(String(30), nullable=False, default=REC_PENDING)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default=PRIORITY_MEDIUM)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.8)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Financial
    expected_savings: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    expected_revenue: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    savings_lower: Mapped[float | None] = mapped_column(Float, nullable=True)
    savings_upper: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Timing (36.5)
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Explainability (36.9-36.10)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason_codes_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Model/Rules
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    rules_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Risk (36.33)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Dedup key (36.24)
    dedup_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # Approval
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Actual outcome (36.36)
    actual_savings: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_revenue: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Extensible
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class FlexibleLoad(Base):
    """36.19: Factory loads that can be shifted in time."""

    __tablename__ = "flexible_loads"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    power_kw: Mapped[float] = mapped_column(Float, nullable=False)
    energy_kwh: Mapped[float] = mapped_column(Float, nullable=False)
    earliest_start: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # Hour
    latest_end: Mapped[int] = mapped_column(Integer, nullable=False, default=23)  # Hour
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    allowed_days_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # [0-6]
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default=PRIORITY_MEDIUM)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class RecommendationHistory(Base):
    """36.35: Audit trail for recommendation status changes."""

    __tablename__ = "recommendation_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    recommendation_id: Mapped[int] = mapped_column(
        ForeignKey("smart_recommendations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    changed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    old_value: Mapped[str | None] = mapped_column(String(30), nullable=True)
    new_value: Mapped[str | None] = mapped_column(String(30), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class OptimizationSnapshot(Base):
    """36.42: Inputs at time of recommendation generation."""

    __tablename__ = "optimization_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    recommendation_id: Mapped[int] = mapped_column(
        ForeignKey("smart_recommendations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    forecast_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    price_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    battery_soc: Mapped[float | None] = mapped_column(Float, nullable=True)
    rules_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    data_quality_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    snapshot_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
