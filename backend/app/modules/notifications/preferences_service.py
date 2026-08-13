from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification_preference import NotificationPreference


def get_or_create_preferences(db: Session, user_id: int) -> NotificationPreference:
    preferences = db.scalar(
        select(NotificationPreference).where(
            NotificationPreference.user_id == user_id
        )
    )

    if preferences:
        return preferences

    preferences = NotificationPreference(user_id=user_id)
    db.add(preferences)
    db.commit()
    db.refresh(preferences)

    return preferences


def update_preferences(db: Session, user_id: int, data) -> NotificationPreference:
    preferences = get_or_create_preferences(db, user_id)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(preferences, field, value)

    db.commit()
    db.refresh(preferences)

    return preferences
