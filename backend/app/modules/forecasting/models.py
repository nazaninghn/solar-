"""
STEP 35: Forecast Engine Data Models.

Forecast header + individual forecast points with confidence intervals.
Model registry for versioning and lifecycle management.
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

# Forecast Types
FORECAST_SOLAR = "SOLAR_GENERATION"
FORECAST_LOAD = "LOAD"
FORECAST_NET_ENERGY = "NET_ENERGY"
FORECAST_BATTERY_SOC = "BATTERY_SOC"
FORECAST_GRID_IMPORT = "GRID_IMPORT"
FORECAST_PRICE = "PRICE"

# Forecast Status
FC_GENERATING = "GENERATING"
FC_READY = "READY"
FC_FAILED = "FAILED"
FC_EXPIRED = "EXPIRED"

# Model Status (35.35)
MODEL_TRAINING = "TRAINING"
MODEL_VALIDATION = "VALIDATION"
MODEL_SHADOW = "SHADOW"
MODEL_PRODUCTION = "PRODUCTION"
MODEL_RETIRED = "RETIRED"


class Forecast(Base):
    """35.5: Forecast header — metadata about a forecast run."""

    __tablename__ = "forecasts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    forecast_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    forecast_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolution: Mapped[str] = mapped_column(String(10), nullable=False, default="1h")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.8)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=FC_READY)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class ForecastPoint(Base):
    """35.5: Individual forecast data points with prediction intervals."""

    __tablename__ = "forecast_points"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    forecast_id: Mapped[int] = mapped_column(
        ForeignKey("forecasts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    predicted_value: Mapped[float] = mapped_column(Float, nullable=False)
    lower_bound: Mapped[float | None] = mapped_column(Float, nullable=True)
    upper_bound: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.8)
    quality: Mapped[str] = mapped_column(String(20), nullable=False, default="GOOD")


class ForecastAccuracy(Base):
    """35.17: Forecast vs Actual comparison records."""

    __tablename__ = "forecast_accuracy"
    __table_args__ = (
        UniqueConstraint("forecast_id", "timestamp", name="uq_forecast_accuracy"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    forecast_id: Mapped[int] = mapped_column(
        ForeignKey("forecasts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    predicted_value: Mapped[float] = mapped_column(Float, nullable=False)
    actual_value: Mapped[float] = mapped_column(Float, nullable=False)
    error: Mapped[float] = mapped_column(Float, nullable=False)
    absolute_error: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ForecastModelRegistry(Base):
    """35.35: Model versioning and lifecycle."""

    __tablename__ = "forecast_model_registry"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=MODEL_PRODUCTION)
    trained_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    mae: Mapped[float | None] = mapped_column(Float, nullable=True)
    rmse: Mapped[float | None] = mapped_column(Float, nullable=True)
    mape: Mapped[float | None] = mapped_column(Float, nullable=True)
    features_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
