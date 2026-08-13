from sqlalchemy import Boolean, ForeignKey
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

    # 23.31: only dashboard is actually wired up. Email/SMS toggles exist
    # so the preferences shape is stable once those channels land, but
    # setting them true today has no effect — 23.32's channel fan-out
    # only has a dashboard implementation.
    email_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sms_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    dashboard_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
