"""
Multi-tenancy decision (Step 4)
-------------------------------
The tenant boundary is the Organization, not the Factory.

- Every Factory belongs to exactly one Organization (organization_id, NOT NULL).
- Every User belongs to exactly one Organization (see app/models/user.py).
- A User can see and act on every Factory that shares their organization_id.
  There is no per-user, per-factory ACL table yet — that is a deliberate
  scope cut. If a customer later needs to restrict a user to a subset of
  factories within their own organization, that becomes a join table
  (user_factory_access) added on top of this, not a redesign of it.
- What a user is *allowed to do* (their role) is a separate concern from
  *which factories they can see* (their organization). Role enforcement
  is implemented in Task 9 (Authorization); this model only defines the
  isolation boundary.
"""

from datetime import datetime, time, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Factory(Base):
    __tablename__ = "factories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)

    industry: Mapped[str] = mapped_column(String(100), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")

    # Nameplate capacity, entered during Factory Setup (Flow 3) —
    # the *actual* Solar/Battery system detail lives in their own tables.
    solar_capacity_kw: Mapped[float] = mapped_column(Float, nullable=True)
    battery_capacity_kwh: Mapped[float] = mapped_column(Float, nullable=True)

    # 21.28-21.29: ROI/payback need an investment figure that didn't
    # exist anywhere in the schema before Step 21.
    solar_installation_cost: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    grid_connection_type: Mapped[str] = mapped_column(String(100), nullable=True)
    electricity_tariff: Mapped[str] = mapped_column(String(100), nullable=True)

    working_hours_start: Mapped[time] = mapped_column(Time, nullable=True)
    working_hours_end: Mapped[time] = mapped_column(Time, nullable=True)

    timezone: Mapped[str] = mapped_column(String(100), nullable=False, default="UTC")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    organization: Mapped["Organization"] = relationship(back_populates="factories")
    solar_system: Mapped["SolarSystem"] = relationship(
        back_populates="factory", uselist=False, cascade="all, delete-orphan"
    )
    battery_system: Mapped["BatterySystem"] = relationship(
        back_populates="factory", uselist=False, cascade="all, delete-orphan"
    )
    energy_meters: Mapped[list["EnergyMeter"]] = relationship(
        back_populates="factory", cascade="all, delete-orphan"
    )
