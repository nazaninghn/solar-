from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.modules.alerts.models import ONCALL_PRIMARY, OnCallSchedule


def get_current_on_call(
    db: Session, factory_id: int, role: str = ONCALL_PRIMARY
) -> User | None:
    now = datetime.now(timezone.utc)

    schedule = db.scalar(
        select(OnCallSchedule)
        .where(
            OnCallSchedule.factory_id == factory_id,
            OnCallSchedule.role == role,
            OnCallSchedule.starts_at <= now,
            OnCallSchedule.ends_at > now,
        )
        .order_by(OnCallSchedule.starts_at.desc())
    )

    if schedule is None:
        return None

    return db.get(User, schedule.user_id)


def create_on_call_shift(
    db: Session, factory_id: int, user_id: int, role: str, starts_at: datetime, ends_at: datetime
) -> OnCallSchedule:
    shift = OnCallSchedule(
        factory_id=factory_id,
        user_id=user_id,
        role=role,
        starts_at=starts_at,
        ends_at=ends_at,
        created_at=datetime.now(timezone.utc),
    )
    db.add(shift)
    db.commit()
    db.refresh(shift)

    return shift


def list_on_call_schedule(db: Session, factory_id: int) -> list[OnCallSchedule]:
    return db.scalars(
        select(OnCallSchedule)
        .where(OnCallSchedule.factory_id == factory_id)
        .order_by(OnCallSchedule.starts_at.desc())
        .limit(50)
    ).all()
