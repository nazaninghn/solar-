from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class DeviceEnergyReading(Base):
    """
    Per-device raw telemetry (17.4's schema, extended in 26.7-26.9).
    Named differently from the existing factory-level
    app.models.energy_reading.EnergyReading (Step 7) — see that decision
    explained where the two would otherwise collide, in
    app/devices/schemas.py.
    """

    __tablename__ = "device_energy_readings"

    __table_args__ = (
        Index(
            "ix_device_energy_readings_factory_timestamp",
            "factory_id",
            "timestamp",
        ),
        # 26.36: replay protection — the same device resending the same
        # timestamp (network retry, duplicate delivery) must not create
        # a second row. The ingestion endpoint upserts against this
        # rather than relying on request-level dedup.
        UniqueConstraint(
            "device_id", "timestamp", name="uq_device_energy_readings_device_timestamp"
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

    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    power_kw: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    energy_kwh: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # 26.3: not every device type has every field (a factory meter has
    # no soc_percent, an inverter has no soc_percent either) — all
    # nullable by design, per 26.7's "همه Deviceها الزاماً همه فیلدها را
    # ندارند".
    voltage: Mapped[float | None] = mapped_column(Float, nullable=True)
    current: Mapped[float | None] = mapped_column(Float, nullable=True)
    frequency: Mapped[float | None] = mapped_column(Float, nullable=True)
    soc_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)

    # 26.8-26.9: manufacturer-specific fields land here verbatim instead
    # of forcing a schema change per manufacturer.
    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
