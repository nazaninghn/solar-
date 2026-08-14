from pydantic import BaseModel


class StartDrillRequest(BaseModel):
    scenario: str
    target_service: str
    environment: str = "staging"


class RecordEventRequest(BaseModel):
    event_type: str
    description: str


class CheckChecklistItemRequest(BaseModel):
    notes: str | None = None
