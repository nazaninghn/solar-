from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.factory import Factory
from app.models.user import User
from app.models.user_factory_access import UserFactoryAccess


def list_users_with_factory_access(db: Session, factory: Factory) -> list[User]:
    """
    30.14-30.16: the reverse direction of can_access_factory — given a
    factory, who should be notified about it? COMPANY_ADMIN/SUPER_ADMIN
    see every factory in their org already (can_access_factory's
    short-circuit); everyone else needs an explicit user_factory_access
    row. Excludes inactive users — a deactivated account shouldn't get
    emailed.
    """
    return db.scalars(
        select(User)
        .outerjoin(
            UserFactoryAccess,
            (UserFactoryAccess.user_id == User.id)
            & (UserFactoryAccess.factory_id == factory.id),
        )
        .where(
            User.organization_id == factory.organization_id,
            User.is_active.is_(True),
            or_(
                User.role.in_(("COMPANY_ADMIN", "SUPER_ADMIN")),
                UserFactoryAccess.id.isnot(None),
            ),
        )
        .distinct()
    ).all()


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
