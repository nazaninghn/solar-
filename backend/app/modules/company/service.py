from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.audit_log import AuditLog
from app.models.factory import Factory
from app.models.organization import Organization
from app.models.refresh_token import RefreshToken
from app.models.user import USER_ROLES, User
from app.models.user_factory_access import UserFactoryAccess
from app.modules.company.schemas import (
    CompanyUserCreate,
    CompanyUserUpdate,
    OrganizationUpdate,
)

# A COMPANY_ADMIN manages their own company's users, but SUPER_ADMIN is a
# platform-level role — nobody should be able to grant it through this API.
ASSIGNABLE_ROLES = tuple(role for role in USER_ROLES if role != "SUPER_ADMIN")


def update_organization(
    db: Session, organization: Organization, data: OrganizationUpdate
) -> Organization:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(organization, field, value)

    db.commit()
    db.refresh(organization)

    return organization


def list_company_users(db: Session, organization_id: int) -> list[User]:
    return db.scalars(
        select(User).where(User.organization_id == organization_id)
    ).all()


def create_company_user(
    db: Session, organization_id: int, data: CompanyUserCreate
) -> User:
    if data.role not in ASSIGNABLE_ROLES:
        raise ValueError(f"Invalid role. Must be one of: {', '.join(ASSIGNABLE_ROLES)}")

    existing_user = db.scalar(select(User).where(User.email == data.email))

    if existing_user:
        raise ValueError("Email already registered")

    user = User(
        organization_id=organization_id,
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
        # Admin-created accounts skip the self-registration email-verify
        # loop — a company admin vouching for the address is treated as
        # equivalent to the user proving it themselves.
        is_verified=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def update_company_user(db: Session, user: User, data: CompanyUserUpdate) -> User:
    updates = data.model_dump(exclude_unset=True)

    if "role" in updates and updates["role"] not in ASSIGNABLE_ROLES:
        raise ValueError(f"Invalid role. Must be one of: {', '.join(ASSIGNABLE_ROLES)}")

    for field, value in updates.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return user


def deactivate_company_user(db: Session, user: User) -> None:
    """Soft-delete (is_active=False), not a hard DELETE — a hard delete
    would orphan this user's audit log / recommendation / financial
    transaction history. Also revokes every active session immediately,
    same as reset_password's reasoning."""
    user.is_active = False

    active_refresh_tokens = db.scalars(
        select(RefreshToken).where(
            RefreshToken.user_id == user.id,
            RefreshToken.revoked_at.is_(None),
        )
    )
    for token_row in active_refresh_tokens:
        token_row.revoked_at = datetime.now(timezone.utc)

    db.commit()


def grant_factory_access(db: Session, user: User, factory: Factory) -> None:
    if factory.organization_id != user.organization_id:
        raise ValueError("Factory does not belong to this user's company")

    existing = db.scalar(
        select(UserFactoryAccess).where(
            UserFactoryAccess.user_id == user.id,
            UserFactoryAccess.factory_id == factory.id,
        )
    )

    if existing:
        return

    db.add(
        UserFactoryAccess(
            user_id=user.id,
            factory_id=factory.id,
            created_at=datetime.now(timezone.utc),
        )
    )
    db.commit()


def revoke_factory_access(db: Session, user_id: int, factory_id: int) -> None:
    existing = db.scalar(
        select(UserFactoryAccess).where(
            UserFactoryAccess.user_id == user_id,
            UserFactoryAccess.factory_id == factory_id,
        )
    )

    if existing:
        db.delete(existing)
        db.commit()


def list_user_factory_access(db: Session, user_id: int) -> list[Factory]:
    return db.scalars(
        select(Factory)
        .join(UserFactoryAccess, UserFactoryAccess.factory_id == Factory.id)
        .where(UserFactoryAccess.user_id == user_id)
    ).all()


def list_audit_log(db: Session, organization_id: int, limit: int = 100) -> list[AuditLog]:
    return db.scalars(
        select(AuditLog)
        .where(AuditLog.organization_id == organization_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    ).all()
