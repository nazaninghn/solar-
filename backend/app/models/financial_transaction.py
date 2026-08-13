from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class FinancialTransaction(Base):
    """21.4-21.6, 21.37-21.38: the per-event ledger that makes every
    number in FinancialRecord auditable back to its source calculation."""

    __tablename__ = "financial_transactions"

    __table_args__ = (
        Index(
            "ix_financial_transactions_factory_timestamp",
            "factory_id",
            "timestamp",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    type: Mapped[str] = mapped_column(String(30), nullable=False)

    energy_kwh: Mapped[float] = mapped_column(Float, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
