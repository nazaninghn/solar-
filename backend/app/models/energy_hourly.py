from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class EnergyHourly(Base):
    __tablename__ = "energy_hourly"

    __table_args__ = (
        UniqueConstraint("factory_id", "hour", name="uq_energy_hourly_factory_hour"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    hour: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    solar_kwh: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    consumption_kwh: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    grid_import_kwh: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    grid_export_kwh: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    battery_charge_kwh: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    battery_discharge_kwh: Mapped[float] = mapped_column(Float, default=0, nullable=False)

    # 17.28 — simplified for MVP: a row only exists if at least one raw
    # reading was found for the hour (so COMPLETE), otherwise no row is
    # created at all, which is how "missing" is represented (17.27) —
    # rather than a fabricated zero-value row. True PARTIAL detection
    # would need an expected-sample-count baseline this system doesn't
    # have yet.
    data_quality: Mapped[str] = mapped_column(String(20), nullable=False, default="COMPLETE")

    # Step 22 addition — a numeric companion to data_quality (22.33-22.34).
    data_completeness: Mapped[float] = mapped_column(
        Float, nullable=False, default=100.0
    )
