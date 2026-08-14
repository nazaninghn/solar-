"""
STEP 50: Data Quality, Energy Reconciliation & Integrity Models.
"""

from datetime import datetime

from sqlalchemy import (
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


class DataQualityRecord(Base):
    """50.18: Per-device data quality tracking."""
    __tablename__ = "data_quality_records"
    __table_args__ = (UniqueConstraint("device_id", "metric", "period_start", name="uq_dq_record"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    metric: Mapped[str] = mapped_column(String(50), nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expected_count: Mapped[int] = mapped_column(Integer, nullable=False)
    received_count: Mapped[int] = mapped_column(Integer, nullable=False)
    invalid_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    late_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class EnergyReconciliation(Base):
    """50.27: Energy balance reconciliation per factory per period."""
    __tablename__ = "energy_reconciliations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    factory_id: Mapped[int] = mapped_column(ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    generation_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    consumption_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    grid_import_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    grid_export_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    battery_charge_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    battery_discharge_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    difference_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    tolerance_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=50)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="MATCHED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DataAnomaly(Base):
    """50.31: Detected data anomalies."""
    __tablename__ = "data_anomalies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    device_id: Mapped[int | None] = mapped_column(ForeignKey("devices.id", ondelete="SET NULL"), nullable=True, index=True)
    factory_id: Mapped[int] = mapped_column(ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True)
    metric: Mapped[str] = mapped_column(String(50), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM")
    detected_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DETECTED")
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DataCorrection(Base):
    """50.34-50.35: Data correction with audit."""
    __tablename__ = "data_corrections"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    factory_id: Mapped[int] = mapped_column(ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True)
    metric: Mapped[str] = mapped_column(String(50), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    old_value: Mapped[float] = mapped_column(Float, nullable=False)
    new_value: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    corrected_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
