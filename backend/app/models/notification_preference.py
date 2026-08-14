from datetime import time

from sqlalchemy import Boolean, ForeignKey, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    battery_alerts: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    price_alerts: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    weather_alerts: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    energy_alerts: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    financial_alerts: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    system_alerts: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # 30.10, added once DEVICE became its own notification type
    # (previously folded into system_alerts) — a device-offline alert
    # and a background-job-failure alert are different enough concerns
    # that a user might reasonably want one without the other.
    device_alerts: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # 30.14-30.18: now wired up — app/notifications/delivery.py fans out
    # to email/SMS per these flags, replacing 23.31's "shape is stable
    # but nothing consumes them yet" state.
    email_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sms_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    dashboard_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    # 30.20: both null means quiet hours are off. Only non-CRITICAL/
    # non-URGENT deliveries are suppressed during the window — see
    # app/notifications/delivery.py's is_within_quiet_hours.
    quiet_hours_start: Mapped[time | None] = mapped_column(Time, nullable=True)
    quiet_hours_end: Mapped[time | None] = mapped_column(Time, nullable=True)
