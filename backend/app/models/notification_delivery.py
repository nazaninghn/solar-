from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class NotificationDelivery(Base):
    """30.26: per-channel delivery tracking, separate from the
    Notification row itself — one notification can fan out to several
    channels (in-app + email + SMS) for several users, each with its
    own independent outcome."""

    __tablename__ = "notification_deliveries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    notification_id: Mapped[int] = mapped_column(
        ForeignKey("notifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # IN_APP / EMAIL / SMS
    channel: Mapped[str] = mapped_column(String(20), nullable=False)

    # PENDING / SENT / DELIVERED / FAILED
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")

    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
