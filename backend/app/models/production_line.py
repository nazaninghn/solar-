from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ProductionLine(Base):
    __tablename__ = "production_lines"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    power_kw: Mapped[float] = mapped_column(Float, nullable=False)
    flexible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    minimum_run_time_hours: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
