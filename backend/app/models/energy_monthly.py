from sqlalchemy import Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class EnergyMonthly(Base):
    """
    Completes the Raw -> Hourly -> Daily -> Monthly pipeline (22.15) —
    nothing built this monthly granularity before Step 22; the existing
    Financial module's get_monthly_history (Step 12) aggregates cost
    figures on the fly from FinancialRecord rather than persisting a
    monthly energy snapshot.
    """

    __tablename__ = "energy_monthly"

    __table_args__ = (
        UniqueConstraint("factory_id", "month", name="uq_energy_monthly_factory_month"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # "YYYY-MM" — matches the existing financial monthly history's own
    # month key format (app/modules/financial/service.get_monthly_history).
    month: Mapped[str] = mapped_column(String(7), nullable=False, index=True)

    solar_kwh: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    consumption_kwh: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    grid_import_kwh: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    grid_export_kwh: Mapped[float] = mapped_column(Float, default=0, nullable=False)

    total_savings: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    total_revenue: Mapped[float] = mapped_column(Float, default=0, nullable=False)

    data_completeness: Mapped[float] = mapped_column(
        Float, nullable=False, default=100.0
    )
