from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ElectricityPrice(Base):
    __tablename__ = "electricity_prices"

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

    buy_price_per_kwh: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    sell_price_per_kwh: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    price_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
