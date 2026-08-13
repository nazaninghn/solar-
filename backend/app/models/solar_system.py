from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class SolarSystem(Base):
    __tablename__ = "solar_systems"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id"),
        nullable=False,
        unique=True,  # one solar system per factory, for now
        index=True,
    )

    installed_capacity_kw: Mapped[float] = mapped_column(Float, nullable=False)
    panel_count: Mapped[int] = mapped_column(Integer, nullable=True)
    inverter_brand: Mapped[str] = mapped_column(String(255), nullable=True)
    efficiency_percent: Mapped[float] = mapped_column(Float, nullable=True)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ACTIVE")
    installation_date: Mapped[date] = mapped_column(Date, nullable=True)

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

    factory: Mapped["Factory"] = relationship(back_populates="solar_system")
