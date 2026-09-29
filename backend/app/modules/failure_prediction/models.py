"""
Failure prediction: persisted assessments and the failure event log.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class FailureRiskAssessment(Base):
    """One scored snapshot of one device. Kept as history (not upserted)
    so trends — PR decline, SOH fade — can be projected forward, and so
    past predictions can be checked against FailureEvent outcomes."""

    __tablename__ = "failure_risk_assessments"
    __table_args__ = (
        Index("ix_failure_risk_device_assessed", "device_id", "assessed_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    factory_id: Mapped[int] = mapped_column(ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    device_type: Mapped[str] = mapped_column(String(50), nullable=False)

    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    # LOW / MEDIUM / HIGH / CRITICAL
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    # "ML+RULES" when the PV model contributed, else "RULES"
    method: Mapped[str] = mapped_column(String(20), nullable=False)

    # ML output — null for non-inverters or when the model couldn't run
    # (ml_status says why).
    ml_status: Mapped[str] = mapped_column(String(30), nullable=False)
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    failure_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    horizon_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fault_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fault_type_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    irradiance_source: Mapped[str | None] = mapped_column(String(20), nullable=True)
    imputed_inputs: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    indicators: Mapped[list] = mapped_column(JSONB, nullable=False)
    top_reason: Mapped[str | None] = mapped_column(String(50), nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    days_to_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    data_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class FailureEvent(Base):
    """An actual failure, recorded by an operator. These are the labels
    no model here has had yet: once enough exist per factory, they're
    what indicator thresholds get calibrated against and what a
    site-specific model gets trained on."""

    __tablename__ = "failure_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    factory_id: Mapped[int] = mapped_column(ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    reported_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
