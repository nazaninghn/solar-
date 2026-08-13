from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class SolarForecast(Base):
    __tablename__ = "solar_forecasts"

    __table_args__ = (
        UniqueConstraint(
            "factory_id", "timestamp", name="uq_solar_forecasts_factory_timestamp"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    expected_power_kw: Mapped[float] = mapped_column(Float, nullable=False)
    expected_energy_kwh: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # Not in 19.21's literal field list, but needed for 19.36's "use
    # last forecast, mark as stale" fallback — without a flag, a caller
    # reading old rows during a weather-API outage can't tell they're
    # looking at stale data versus a freshly generated forecast.
    is_stale: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
