from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_accessible_factory, get_current_user
from app.database.session import get_db
from app.models.factory import Factory
from app.models.user import User
from app.modules.notifications.preferences_schemas import (
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
)
from app.modules.notifications.preferences_service import (
    get_or_create_preferences,
    update_preferences,
)
from app.modules.notifications.schemas import (
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from app.modules.notifications.service import (
    acknowledge_notification,
    dismiss_notification,
    get_notifications,
    get_unread_count,
    mark_all_as_read,
    mark_as_read,
    resolve_notification,
)

# Factory-scoped endpoints (14.10, 14.12, 14.14, 23.21-23.22).
router = APIRouter(
    prefix="/api/v1/factories/{factory_id}/notifications",
    tags=["Notifications"],
)


@router.get("", response_model=NotificationListResponse)
def list_notifications(
    status: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    items, total = get_notifications(
        db=db,
        factory_id=factory.id,
        status_filter=status,
        severity_filter=severity,
        type_filter=type,
        page=page,
        limit=limit,
    )

    return NotificationListResponse(items=items, total=total, page=page, limit=limit)


@router.get("/unread-count", response_model=UnreadCountResponse)
def notifications_unread_count(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    return {"count": get_unread_count(db=db, factory_id=factory.id)}


@router.patch("/read-all", status_code=204)
def notifications_mark_all_as_read(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    mark_all_as_read(db=db, factory_id=factory.id)


# 14.13's endpoint is intentionally NOT nested under /factories/{factory_id}
# — see the docstring on notifications.service._get_owned_notification
# for how ownership is still enforced without a factory_id in the path.
notification_router = APIRouter(
    prefix="/api/v1/notifications",
    tags=["Notifications"],
)


@notification_router.patch("/{notification_id}/read", response_model=NotificationResponse)
def notification_mark_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return mark_as_read(db=db, current_user=current_user, notification_id=notification_id)


@notification_router.patch(
    "/{notification_id}/acknowledge", response_model=NotificationResponse
)
def notification_acknowledge(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return acknowledge_notification(
        db=db, current_user=current_user, notification_id=notification_id
    )


@notification_router.patch(
    "/{notification_id}/resolve", response_model=NotificationResponse
)
def notification_resolve(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return resolve_notification(
        db=db, current_user=current_user, notification_id=notification_id
    )


@notification_router.patch(
    "/{notification_id}/dismiss", response_model=NotificationResponse
)
def notification_dismiss(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return dismiss_notification(
        db=db, current_user=current_user, notification_id=notification_id
    )


@notification_router.get(
    "/preferences", response_model=NotificationPreferenceResponse
)
def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_or_create_preferences(db=db, user_id=current_user.id)


@notification_router.patch(
    "/preferences", response_model=NotificationPreferenceResponse
)
def update_notification_preferences(
    data: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return update_preferences(db=db, user_id=current_user.id, data=data)
