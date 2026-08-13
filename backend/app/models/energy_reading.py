from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class EnergyReading(Base):
    __tablename__ = "energy_readings"

    __table_args__ = (
        # 26.\ (aggregation gap fix): device-derived rows are one
        # canonical row per factory per hour (timestamp = hour_start),
        # upserted by the sync job — this constraint is what makes that
        # upsert idempotent. Manual entries (source="MANUAL") aren't
        # expected to collide on this pair in practice, so the shared
        # constraint doesn't change their existing behavior.
        UniqueConstraint(
            "factory_id", "timestamp", "source",
            name="uq_energy_readings_factory_timestamp_source",
        ),
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

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    # 26's aggregation-gap fix: distinguishes Step 7's manual/API entries
    # from rows the device-telemetry sync job derives via time-weighted
    # integration of DeviceEnergyReading — same aggregation pipeline
    # downstream either way, but this makes the provenance inspectable.
    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="MANUAL",
    )

    solar_generation_kwh: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    consumption_kwh: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    grid_import_kwh: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    grid_export_kwh: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    battery_charge_kwh: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    battery_discharge_kwh: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    battery_soc_percent: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
