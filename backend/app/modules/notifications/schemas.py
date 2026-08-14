from datetime import datetime

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: int
    type: str
    severity: str
    priority: str
    status: str
    title: str
    message: str
    is_read: bool
    value: float | None
    threshold: float | None
    unit: str | None
    source: str | None
    alert_metadata: dict | None
    created_at: datetime
    read_at: datetime | None
    acknowledged_by: int | None
    acknowledged_at: datetime | None
    resolved_at: datetime | None

    model_config = {"from_attributes": True}


class UnreadCountResponse(BaseModel):
    count: int


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    page: int
    limit: int
