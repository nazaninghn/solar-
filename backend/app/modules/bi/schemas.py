from pydantic import BaseModel


class SignupDay(BaseModel):
    date: str
    signups: int


class ActivationRateResponse(BaseModel):
    cohort_size: int
    activated_count: int
    activation_rate_percent: float


class FunnelStage(BaseModel):
    stage: str
    count: int


class NorthStarResponse(BaseModel):
    weekly_active_factories: int
    active_organizations: int


class CohortRetentionEntry(BaseModel):
    month_offset: int
    retained_percent: float | None


class CohortResponse(BaseModel):
    cohort_month: str
    cohort_size: int
    retention: list[CohortRetentionEntry]


class RevenueResponse(BaseModel):
    mrr: float
    arr: float
    churn: dict
    ltv: dict


class SegmentationResponse(BaseModel):
    by_plan: list[dict]
    by_industry: list[dict]
    by_size: list[dict]


class BiDashboardResponse(BaseModel):
    north_star: NorthStarResponse
    signups_last_30_days: int
    activation: ActivationRateResponse
    funnel: list[FunnelStage]
    revenue: RevenueResponse
    segmentation: SegmentationResponse
