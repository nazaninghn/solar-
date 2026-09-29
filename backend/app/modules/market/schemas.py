from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class PricePoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    timestamp: datetime
    ptf_try_mwh: float | None
    ptf_usd_mwh: float | None
    ptf_eur_mwh: float | None
    smf_try_mwh: float | None


class ForecastPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    timestamp: datetime
    p10_try_mwh: float
    p50_try_mwh: float
    p90_try_mwh: float


class ForecastResponse(BaseModel):
    delivery_date: date
    model_version: str | None
    issued_at: datetime | None
    points: list[ForecastPoint]
    actual: list[PricePoint]


class MarketStatusResponse(BaseModel):
    epias_configured: bool
    price_rows: int
    first_price_at: datetime | None
    last_price_at: datetime | None
    next_delivery_date: date
    model: dict | None


class SyncRequest(BaseModel):
    days: int = Field(default=7, ge=1, le=1200)


class OfferRequest(BaseModel):
    delivery_date: date | None = None
    mode: str = Field(default="GOP_BID", pattern="^(GOP_BID|NET_METERING)$")
    min_price_try_mwh: float = Field(default=0.0, ge=0)


class OfferRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    tier: int
    mode: str
    action: str
    quantity_mwh: float
    price_try_mwh: float | None
    expected_ptf_try_mwh: float | None
    expected_revenue_try: float | None
    revenue_p10_try: float | None
    revenue_p90_try: float | None
    status: str
    inputs: dict | None


class OfferResponse(BaseModel):
    factory_id: int
    delivery_date: date
    gate_closure: datetime
    status: str | None
    total_quantity_mwh: float
    expected_revenue_try: float
    revenue_p10_try: float
    revenue_p90_try: float
    rows: list[OfferRow]
    notes: list[str]
