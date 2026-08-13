from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class FinancialRecord(Base):
    __tablename__ = "financial_records"

    __table_args__ = (
        # One record per factory per day — the "Daily Financial Record"
        # concept in 12.2 only makes sense as a single row; without this,
        # recomputing the same day would silently create duplicates.
        UniqueConstraint("factory_id", "date", name="uq_financial_records_factory_date"),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    solar_savings: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    grid_purchase_cost: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    battery_savings: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    energy_sales_revenue: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    total_savings: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    net_energy_cost: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    # Step 21 additions — this record already was Step 21's "daily
    # snapshot" (21.35) in everything but name; extended in place rather
    # than adding a second, near-duplicate daily table.
    solar_generation_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    solar_used_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    grid_import_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    grid_export_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0)

    battery_degradation_cost: Mapped[float] = mapped_column(
        Float, nullable=False, default=0
    )
    load_shift_savings: Mapped[float] = mapped_column(
        Float, nullable=False, default=0
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
