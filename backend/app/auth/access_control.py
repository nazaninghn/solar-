from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.factory import Factory
from app.models.user import User
from app.models.user_factory_access import UserFactoryAccess


def user_has_factory_access(db: Session, user_id: int, factory_id: int) -> bool:
    return (
        db.scalar(
            select(UserFactoryAccess).where(
                UserFactoryAccess.user_id == user_id,
                UserFactoryAccess.factory_id == factory_id,
            )
        )
        is not None
    )


def can_access_factory(db: Session, user: User, factory: Factory) -> bool:
    """24.26, verbatim logic."""
    if user.role == "SUPER_ADMIN":
        return True

    if factory.organization_id != user.organization_id:
        return False

    if user.role == "COMPANY_ADMIN":
        return True

    return user_has_factory_access(db, user.id, factory.id)
