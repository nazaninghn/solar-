"""
STEP 51: Performance & Scalability Models.

Capacity metrics, Performance budgets, Tenant quotas, Circuit breaker state.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class CapacityMetric(Base):
    """51.51: Capacity planning metrics."""
    __tablename__ = "capacity_metrics"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    metric: Mapped[str] = mapped_column(String(100), nullable=False)
    current_value: Mapped[float] = mapped_column(Float, nullable=False)
    current_capacity: Mapped[float] = mapped_column(Float, nullable=False)
    target_capacity: Mapped[float | None] = mapped_column(Float, nullable=True)
    warning_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    critical_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(20), nullable=False, default="count")
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PerformanceBudget(Base):
    """51.52: Performance targets per endpoint."""
    __tablename__ = "performance_budgets"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    endpoint: Mapped[str] = mapped_column(String(200), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    p50_target_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=200)
    p95_target_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=500)
    p99_target_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    max_error_rate_pct: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TenantQuota(Base):
    """51.59: Per-organization resource quotas."""
    __tablename__ = "tenant_quotas"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    max_factories: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    max_devices: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    max_users: Mapped[int] = mapped_column(Integer, nullable=False, default=25)
    max_api_requests_per_min: Mapped[int] = mapped_column(Integer, nullable=False, default=600)
    max_telemetry_per_min: Mapped[int] = mapped_column(Integer, nullable=False, default=5000)
    max_storage_gb: Mapped[float] = mapped_column(Float, nullable=False, default=10.0)
    max_reports_per_day: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CircuitBreakerState(Base):
    """51.37: Circuit breaker state for external services."""
    __tablename__ = "circuit_breaker_states"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    service_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    state: Mapped[str] = mapped_column(String(20), nullable=False, default="CLOSED")  # CLOSED, OPEN, HALF_OPEN
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    half_open_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    recovery_timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
