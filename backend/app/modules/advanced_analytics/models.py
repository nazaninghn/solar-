"""
STEP 45: Advanced Analytics Models.

Energy KPIs, Hourly/Daily/Monthly Aggregations, Forecast Records,
Anomalies, Device Performance, Recommendation Impact.
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


class EnergyKPI(Base):
    """45.4: Computed energy KPIs per factory per period."""
    __tablename__ = "energy_kpis"
    __table_args__ = (UniqueConstraint("factory_id", "period_start", "period_end", name="uq_energy_kpi"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    factory_id: Mapped[int] = mapped_column(ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    solar_generation_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    consumption_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    grid_import_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    grid_export_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    battery_charge_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    battery_discharge_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    self_consumption_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    solar_coverage_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    grid_dependency_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    renewable_share: Mapped[float | None] = mapped_column(Float, nullable=True)
    peak_demand_kw: Mapped[float | None] = mapped_column(Float, nullable=True)
    load_factor: Mapped[float | None] = mapped_column(Float, nullable=True)
    calculation_version: Mapped[str] = mapped_column(String(20), nullable=False, default="kpi-v1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class HourlyEnergyMetric(Base):
    """45.12: Hourly energy aggregation."""
    __tablename__ = "hourly_energy_metrics"
    __table_args__ = (UniqueConstraint("factory_id", "hour", name="uq_hourly_energy"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    factory_id: Mapped[int] = mapped_column(ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True)
    hour: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    solar_generation_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    consumption_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    grid_import_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    grid_export_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    battery_charge_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    battery_discharge_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    peak_power_kw: Mapped[float | None] = mapped_column(Float, nullable=True)
    average_power_kw: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DailyEnergyMetric(Base):
    """45.13: Daily energy aggregation."""
    __tablename__ = "daily_energy_metrics"
    __table_args__ = (UniqueConstraint("factory_id", "date", name="uq_daily_energy_metric"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    factory_id: Mapped[int] = mapped_column(ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True)
    date: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    solar_generation_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    consumption_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    grid_import_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    grid_export_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    battery_charge_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    battery_discharge_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    peak_demand_kw: Mapped[float | None] = mapped_column(Float, nullable=True)
    solar_coverage_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    self_consumption_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ForecastRecord(Base):
    """45.16: Individual forecast vs actual for evaluation."""
    __tablename__ = "forecast_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    factory_id: Mapped[int] = mapped_column(ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True)
    forecast_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    target_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    predicted_value: Mapped[float] = mapped_column(Float, nullable=False)
    actual_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(20), nullable=False, default="kWh")
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Anomaly(Base):
    """45.28: Detected anomalies."""
    __tablename__ = "anomalies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    factory_id: Mapped[int] = mapped_column(ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM")
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    observed_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    deviation: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DETECTED")
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class DevicePerformance(Base):
    """45.33: Device performance metrics per period."""
    __tablename__ = "device_performance"
    __table_args__ = (UniqueConstraint("device_id", "period_start", name="uq_device_perf"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    availability: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    efficiency: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    production_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    performance_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RecommendationImpact(Base):
    """45.50: Recommendation financial impact measurement."""
    __tablename__ = "recommendation_impacts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    recommendation_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    factory_id: Mapped[int] = mapped_column(ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True)
    baseline_cost: Mapped[float] = mapped_column(Float, nullable=False)
    actual_cost: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_saving: Mapped[float] = mapped_column(Float, nullable=False)
    realized_saving: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="EUR")
    measurement_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    measurement_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
