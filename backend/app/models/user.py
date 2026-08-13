from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

# Role vocabulary from the product brief. Kept as a plain String (not a
# native Postgres ENUM) so adding a role later is a data change, not a
# migration that rewrites a type. Enforcement of what each role can do
# is Task 9 (Authorization) — this column only records the value.
#
# Step 24 replaces the original OWNER/ADMIN/OPERATOR/FINANCE_MANAGER
# vocabulary with this richer hierarchy (SUPER_ADMIN is genuinely new —
# nothing maps to it). The migration backfills existing rows:
# OWNER/ADMIN -> COMPANY_ADMIN, OPERATOR -> FACTORY_MANAGER,
# FINANCE_MANAGER -> FINANCIAL_MANAGER, ENERGY_MANAGER/VIEWER unchanged.
USER_ROLES = (
    "SUPER_ADMIN",
    "COMPANY_ADMIN",
    "FACTORY_MANAGER",
    "ENERGY_MANAGER",
    "FINANCIAL_MANAGER",
    "VIEWER",
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)

    role: Mapped[str] = mapped_column(String(50), nullable=False, default="VIEWER")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

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

    organization: Mapped["Organization"] = relationship(back_populates="users")
