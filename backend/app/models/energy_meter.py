"""
This table records that a meter exists and is connected — device
metadata only. The time-series readings it produces (solar_generation_kwh,
consumption_kwh, grid_import_kwh, grid_export_kwh, ...) are a separate
concern (Task 13, EnergyReading) and are not part of this step.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

# A factory can have more than one meter (grid import, grid export,
# sub-metered production lines, ...), so this is many-to-one to Factory.
METER_TYPES = (
    "GRID_IMPORT",
    "GRID_EXPORT",
    "SOLAR_PRODUCTION",
    "CONSUMPTION",
    "SUB_METER",
)


class EnergyMeter(Base):
    __tablename__ = "energy_meters"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id"),
        nullable=False,
        index=True,
    )

    meter_type: Mapped[str] = mapped_column(String(50), nullable=False)
    manufacturer: Mapped[str] = mapped_column(String(255), nullable=True)
    model: Mapped[str] = mapped_column(String(255), nullable=True)
    serial_number: Mapped[str] = mapped_column(String(255), nullable=True)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="CONNECTED")

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

    factory: Mapped["Factory"] = relationship(back_populates="energy_meters")
