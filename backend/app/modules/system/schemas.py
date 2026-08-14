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


class RequestMetrics(BaseModel):
    total_requests: int
    total_errors_5xx: int
    error_rate_percent: float
    average_duration_ms: float
    p50_duration_ms: float
    p90_duration_ms: float
    p95_duration_ms: float
    p99_duration_ms: float
    bucket_counts: dict[str, int]
    uptime_seconds: float


class SloStatus(BaseModel):
    name: str
    sli: str
    actual_value: float
    target_value: float
    unit: str
    compliant: bool
    error_budget_consumed_percent: float | None = None


class SloStatusListResponse(BaseModel):
    slos: list[SloStatus]


class DeviceStatusCounts(BaseModel):
    total: int
    online: int
    warning: int
    offline: int


class DatabasePoolStats(BaseModel):
    pool_size: int
    checked_out: int
    checked_in: int
    overflow: int


class ExternalApiStats(BaseModel):
    request_count: int
    success_count: int
    failure_count: int
    timeout_count: int
    success_rate_percent: float
    average_latency_ms: float
    status: str


class SystemMetricsResponse(BaseModel):
    requests: RequestMetrics
    devices: DeviceStatusCounts
    database: DatabasePoolStats
    external_apis: dict[str, ExternalApiStats]


class ApiHealthStatus(BaseModel):
    status: str
    average_latency_ms: float
    error_rate_percent: float


class DatabaseHealthStatus(BaseModel):
    status: str


class SchedulerHealthStatus(BaseModel):
    status: str
    jobs_total: int
    jobs_failed: int
    failed_job_names: list[str]


class DeviceHealthStatus(BaseModel):
    status: str
    total: int
    online: int
    warning: int
    offline: int


class ExternalApisHealthStatus(BaseModel):
    status: str
    providers: dict[str, ExternalApiStats]


class SystemHealthResponse(BaseModel):
    overall_status: str
    api: ApiHealthStatus
    database: DatabaseHealthStatus
    scheduler: SchedulerHealthStatus
    devices: DeviceHealthStatus
    external_apis: ExternalApisHealthStatus
