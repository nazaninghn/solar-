"""
STEP 34: Data Pipeline Models.

Raw Telemetry, Metric Catalog, Aggregations, Daily Summary, Data Quality.
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


class RawTelemetry(Base):
    """34.4: Raw telemetry as received from device — never modified."""

    __tablename__ = "raw_telemetry"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    device_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    topic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    message_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    ingestion_status: Mapped[str] = mapped_column(String(20), nullable=False, default="RECEIVED")
    error_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MetricCatalog(Base):
    """34.6: Central metric definitions — standard names, units, ranges."""

    __tablename__ = "metric_catalog"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    key: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    data_type: Mapped[str] = mapped_column(String(20), nullable=False, default="float")
    min_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    aggregation: Mapped[str] = mapped_column(String(20), nullable=False, default="avg")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Telemetry5m(Base):
    """34.15: 5-minute aggregation bucket."""

    __tablename__ = "telemetry_5m"
    __table_args__ = (
        UniqueConstraint("factory_id", "device_id", "metric", "bucket_start", name="uq_telemetry_5m"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metric: Mapped[str] = mapped_column(String(50), nullable=False)
    bucket_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    min_value: Mapped[float] = mapped_column(Float, nullable=False)
    max_value: Mapped[float] = mapped_column(Float, nullable=False)
    avg_value: Mapped[float] = mapped_column(Float, nullable=False)
    sum_value: Mapped[float] = mapped_column(Float, nullable=False)
    last_value: Mapped[float] = mapped_column(Float, nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quality_summary: Mapped[str] = mapped_column(String(20), nullable=False, default="GOOD")


class TelemetryHourly(Base):
    """34.15: Hourly aggregation."""

    __tablename__ = "telemetry_hourly"
    __table_args__ = (
        UniqueConstraint("factory_id", "device_id", "metric", "bucket_start", name="uq_telemetry_hourly"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metric: Mapped[str] = mapped_column(String(50), nullable=False)
    bucket_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    min_value: Mapped[float] = mapped_column(Float, nullable=False)
    max_value: Mapped[float] = mapped_column(Float, nullable=False)
    avg_value: Mapped[float] = mapped_column(Float, nullable=False)
    sum_value: Mapped[float] = mapped_column(Float, nullable=False)
    last_value: Mapped[float] = mapped_column(Float, nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quality_summary: Mapped[str] = mapped_column(String(20), nullable=False, default="GOOD")


class DailyEnergySummary(Base):
    """34.22: Factory daily energy summary — the core KPI record."""

    __tablename__ = "daily_energy_summary"
    __table_args__ = (
        UniqueConstraint("factory_id", "date", name="uq_daily_energy_summary"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # YYYY-MM-DD

    solar_generation_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    factory_consumption_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    grid_import_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    grid_export_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    battery_charge_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    battery_discharge_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)

    estimated_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    estimated_savings: Mapped[float] = mapped_column(Float, nullable=False, default=0)

    peak_power_kw: Mapped[float | None] = mapped_column(Float, nullable=True)
    peak_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    data_quality: Mapped[str] = mapped_column(String(20), nullable=False, default="GOOD")
    data_quality_score: Mapped[int] = mapped_column(Integer, nullable=False, default=100)


class DataQualityLog(Base):
    """34.24: Per-factory data quality tracking."""

    __tablename__ = "data_quality_log"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[str] = mapped_column(String(10), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-100
    completeness: Mapped[float] = mapped_column(Float, nullable=False)
    freshness: Mapped[float] = mapped_column(Float, nullable=False)
    validity: Mapped[float] = mapped_column(Float, nullable=False)
    device_coverage: Mapped[float] = mapped_column(Float, nullable=False)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
