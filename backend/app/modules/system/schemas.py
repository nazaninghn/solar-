from datetime import datetime

from pydantic import BaseModel


class JobStatusResponse(BaseModel):
    name: str
    status: str
    last_run: datetime | None
    duration_ms: int | None
    error_message: str | None


class JobStatusListResponse(BaseModel):
    jobs: list[JobStatusResponse]


class ScenarioRequest(BaseModel):
    scenario: str


class ScenarioResponse(BaseModel):
    scenario: str
    valid_scenarios: list[str]
