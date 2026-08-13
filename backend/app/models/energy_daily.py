from datetime import date as date_type, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class EnergyDaily(Base):
    __tablename__ = "energy_daily"

    __table_args__ = (
        UniqueConstraint("factory_id", "date", name="uq_energy_daily_factory_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)

    solar_kwh: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    consumption_kwh: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    grid_import_kwh: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    grid_export_kwh: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    battery_charge_kwh: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    battery_discharge_kwh: Mapped[float] = mapped_column(Float, default=0, nullable=False)

    data_quality: Mapped[str] = mapped_column(String(20), nullable=False, default="COMPLETE")

    # Step 22 additions.
    data_completeness: Mapped[float] = mapped_column(
        Float, nullable=False, default=100.0
    )
    peak_demand_kw: Mapped[float | None] = mapped_column(Float, nullable=True)
    peak_demand_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    peak_solar_kw: Mapped[float | None] = mapped_column(Float, nullable=True)
