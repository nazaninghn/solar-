"""
STEP 79: Compliance & Governance models.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base

# 79.33: currently only "organization" is a real target — the common
# case (a customer in litigation, a subpoena) is "hold everything for
# this company," not one row in one table. resource_type is a string,
# not a fixed enum, so a narrower target (e.g. "factory") can be added
# later without a schema change.
HOLD_RESOURCE_TYPE_ORGANIZATION = "organization"


class LegalHold(Base):
    """
    79.33: suspends retention purges for a resource while active.
    Checked by app.jobs.retention_jobs before any delete, and by
    app.modules.auth.data_rights.delete_own_account before an
    organization's last data can be anonymized/removed.
    """

    __tablename__ = "legal_holds"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    resource_type: Mapped[str] = mapped_column(String(30), nullable=False)
    resource_id: Mapped[int] = mapped_column(nullable=False, index=True)

    reason: Mapped[str] = mapped_column(Text, nullable=False)

    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    released_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Vendor(Base):
    """79.41-79.44: third-party governance — purpose, data access,
    risk tier, and contract status for anything this platform sends
    data to or relies on. No prior tracking existed for this at all
    (the weather provider was hardcoded config with no governance
    record)."""

    __tablename__ = "vendors"

    RISK_TIERS = ("CRITICAL", "HIGH", "MEDIUM", "LOW")
    STATUSES = ("ACTIVE", "UNDER_REVIEW", "OFFBOARDING", "OFFBOARDED")

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    data_access_description: Mapped[str] = mapped_column(Text, nullable=False)
    risk_tier: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")

    contract_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dpa_signed: Mapped[bool] = mapped_column(nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
