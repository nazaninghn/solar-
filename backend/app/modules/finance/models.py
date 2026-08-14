"""
STEP 37: Financial Engine Models.

Price, Tariff, Energy Ledger, Financial Ledger, Daily/Monthly Summary, Reports.
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

# Tariff Types (37.5)
TARIFF_TIME_OF_USE = "TIME_OF_USE"
TARIFF_FLAT = "FLAT"
TARIFF_TIERED = "TIERED"
TARIFF_DEMAND = "DEMAND_BASED"
TARIFF_CUSTOM = "CUSTOM"

# Price Direction
DIRECTION_IMPORT = "IMPORT"
DIRECTION_EXPORT = "EXPORT"

# Ledger Types (37.14)
LEDGER_GRID_COST = "GRID_COST"
LEDGER_EXPORT_REVENUE = "EXPORT_REVENUE"
LEDGER_SAVINGS = "SAVINGS"
LEDGER_BATTERY_COST = "BATTERY_COST"
LEDGER_DEMAND_CHARGE = "DEMAND_CHARGE"
LEDGER_ADJUSTMENT = "ADJUSTMENT"


class EnergyPrice(Base):
    """37.4: Energy price records with versioning."""

    __tablename__ = "energy_prices_v2"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    market: Mapped[str] = mapped_column(String(50), nullable=False, default="SPOT")
    direction: Mapped[str] = mapped_column(String(10), nullable=False)  # IMPORT/EXPORT
    price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="EUR")
    unit: Mapped[str] = mapped_column(String(20), nullable=False, default="kWh")
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="v1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Tariff(Base):
    """37.5: Tariff definitions with effective dating."""

    __tablename__ = "tariffs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False, default=TARIFF_TIME_OF_USE)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="EUR")
    unit: Mapped[str] = mapped_column(String(20), nullable=False, default="kWh")
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="v1")
    rules_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # TOU periods, tiers, etc.
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class EnergyLedger(Base):
    """37.13: Energy flow tracking for audit."""

    __tablename__ = "energy_ledger"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(30), nullable=False)  # SOLAR, GRID, BATTERY
    destination: Mapped[str] = mapped_column(String(30), nullable=False)  # FACTORY, GRID, BATTERY
    energy_kwh: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(10), nullable=False, default="kWh")
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="EUR")
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class FinancialLedger(Base):
    """37.14: Financial transaction ledger."""

    __tablename__ = "financial_ledger"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="EUR")
    energy_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="CONFIRMED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DailyFinancialSummary(Base):
    """37.17: Daily financial summary."""

    __tablename__ = "daily_financial_summary"
    __table_args__ = (
        UniqueConstraint("factory_id", "date", "calculation_version", name="uq_daily_financial"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    grid_import_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    export_revenue: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    solar_value: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    battery_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    total_energy_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    baseline_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    estimated_savings: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    net_energy_benefit: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="EUR")
    calculation_version: Mapped[str] = mapped_column(String(20), nullable=False, default="v1")
    tariff_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    price_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    data_quality: Mapped[str] = mapped_column(String(20), nullable=False, default="GOOD")


class MonthlyFinancialSummary(Base):
    """37.18: Monthly financial summary."""

    __tablename__ = "monthly_financial_summary"
    __table_args__ = (
        UniqueConstraint("factory_id", "month", name="uq_monthly_financial"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    month: Mapped[str] = mapped_column(String(7), nullable=False, index=True)  # YYYY-MM
    grid_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    export_revenue: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    solar_value: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    battery_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    savings: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    net_benefit: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    vs_previous_month: Mapped[float | None] = mapped_column(Float, nullable=True)
    vs_baseline: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="EUR")


class FinancialReport(Base):
    """37.33: Generated financial reports with frozen snapshots."""

    __tablename__ = "financial_reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(30), nullable=False, default="MONTHLY")
    period_start: Mapped[str] = mapped_column(String(10), nullable=False)
    period_end: Mapped[str] = mapped_column(String(10), nullable=False)
    calculation_version: Mapped[str] = mapped_column(String(20), nullable=False)
    tariff_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    price_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="GENERATED")
    snapshot_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
