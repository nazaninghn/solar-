"""
STEP 78: FinOps & Cost Optimization models.
"""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base

# 78.1: no billing API integration exists (Render doesn't expose one
# this codebase safely calls without stored credentials, and none was
# requested) — real infrastructure cost has to come from a human
# reading their actual invoice and entering it here. Everything
# downstream (cost attribution, budget alerts) is a real calculation
# against these admin-entered numbers, not a fabricated estimate.
COST_CATEGORIES = ("COMPUTE", "DATABASE", "STORAGE", "THIRD_PARTY", "NETWORK", "LOGGING")


class InfrastructureCost(Base):
    __tablename__ = "infrastructure_costs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    monthly_cost_usd: Mapped[float] = mapped_column(Float, nullable=False)

    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class BudgetThreshold(Base):
    """78: a monthly USD ceiling — checked by app.jobs.finops_jobs'
    budget alert job against the sum of active InfrastructureCost rows
    (78's "Budget Alerts")."""

    __tablename__ = "budget_thresholds"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    monthly_budget_usd: Mapped[float] = mapped_column(Float, nullable=False)
    warning_percent: Mapped[float] = mapped_column(Float, nullable=False, default=80.0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
