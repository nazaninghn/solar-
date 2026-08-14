from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class AuditLog(Base):
    """
    24.33-24.34: a general admin-action log, distinct from Step 20's
    RecommendationAuditLog — that one is narrowly scoped to
    accept/reject decisions on recommendations; this one covers any
    mutating admin action (user management, factory settings, etc).
    """

    __tablename__ = "audit_logs"

    __table_args__ = (
        # 84: company/service.py's list_audit_log (the company audit-log
        # page) always filters by organization_id then orders by
        # created_at DESC — the individual organization_id index alone
        # still forces a sort over every matching row; this composite
        # lets Postgres walk the index in the right order directly.
        Index("ix_audit_logs_org_created_at", "organization_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
