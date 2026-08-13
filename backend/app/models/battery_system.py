from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class BatterySystem(Base):
    __tablename__ = "battery_systems"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id"),
        nullable=False,
        unique=True,  # one battery system per factory, for now
        index=True,
    )

    capacity_kwh: Mapped[float] = mapped_column(Float, nullable=False)
    usable_capacity_kwh: Mapped[float] = mapped_column(Float, nullable=True)

    state_of_charge_percent: Mapped[float] = mapped_column(Float, nullable=True)
    state_of_health_percent: Mapped[float] = mapped_column(Float, nullable=True)
    temperature_c: Mapped[float] = mapped_column(Float, nullable=True)

    cycle_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    charge_rate_kw: Mapped[float] = mapped_column(Float, nullable=True)
    discharge_rate_kw: Mapped[float] = mapped_column(Float, nullable=True)

    # 18.10-18.11: reserve bounds so the energy engine never plans to
    # discharge a battery to 0% or charge it past a safe ceiling.
    min_soc_percent: Mapped[float] = mapped_column(Float, nullable=False, default=10)
    max_soc_percent: Mapped[float] = mapped_column(Float, nullable=False, default=95)

    # Real per-battery round-trip efficiency. Steps 11 and 12 currently
    # hardcode a 90% MVP placeholder in two separate places rather than
    # reading this column — that's a pre-existing gap this step doesn't
    # fix (out of scope here), noted for a future cleanup pass.
    efficiency_percent: Mapped[float] = mapped_column(Float, nullable=False, default=90)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="IDLE")

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

    factory: Mapped["Factory"] = relationship(back_populates="battery_system")
