from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    factory_id: Mapped[int] = mapped_column(
        ForeignKey(
            "factories.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=True,
        index=True,
    )

    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    deduplication_key: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    # Step 23 additions.
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="UNREAD")

    # 30.29: LOW/NORMAL/HIGH/URGENT — deliberately separate from
    # severity (INFO/WARNING/CRITICAL/SUCCESS). Severity describes how
    # bad the underlying condition is; priority describes how urgently
    # a human should be interrupted about it. They usually correlate
    # (see notifications/engine.py's default mapping) but a
    # recommendation is INFO-severity yet NORMAL-priority, not LOW —
    # it's actionable, just not describing anything broken.
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="NORMAL")

    # 30.24: recorded separately from resolved_at — acknowledging means
    # "a human has seen this and is on it", not "the underlying issue
    # is fixed". Both can be true at different times for the same alert.
    acknowledged_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # 30.13: set once this notification has triggered an escalation, so
    # the escalation job never sends a second escalation for the same
    # unacknowledged alert.
    escalated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # 23.19's fingerprint components — kept separate from
    # deduplication_key (Step 14, date-scoped) since cooldown-based dedup
    # (23.18) needs to check "was this rule triggered recently", not
    # "was it triggered today".
    rule_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)

    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # 23.35: recommended_action / related_resource / related_resource_id
    # live in here rather than as dedicated columns — this is
    # per-alert-type structured data with no shared shape across types.
    alert_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
