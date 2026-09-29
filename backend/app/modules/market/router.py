"""Day-ahead market API: PTF prices/forecasts and factory sell offers."""

from datetime import date, datetime, timedelta, timezone

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.auth.permissions import MANAGE_COMPANY_SETTINGS, MANAGE_FINANCIAL
from app.core.dependencies import get_accessible_factory, get_current_user
from app.database.session import get_db
from app.models.factory import Factory
from app.models.user import User
from app.modules.market import epias_client, forecasting, service
from app.modules.market.models import MarketPrice, SellOffer
from app.modules.market.schemas import (
    ForecastPoint,
    ForecastResponse,
    MarketStatusResponse,
    OfferRequest,
    OfferResponse,
    OfferRow,
    PricePoint,
    SyncRequest,
)

router = APIRouter(prefix="/api/v1/market", tags=["Day-Ahead Market"])
offer_router = APIRouter(prefix="/api/v1/factories/{factory_id}/sell-offers", tags=["Day-Ahead Market"])


def _gate_closure(delivery_date: date) -> datetime:
    """GÖP gate closure: 12:30 Turkey time on the day before delivery."""
    ts = pd.Timestamp(delivery_date - timedelta(days=1)).tz_localize(forecasting.TR_TZ) + pd.Timedelta(hours=12, minutes=30)
    return ts.tz_convert("UTC").to_pydatetime()


@router.get("/status", response_model=MarketStatusResponse)
def market_status(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    count, first, last = db.execute(
        select(func.count(MarketPrice.id), func.min(MarketPrice.timestamp), func.max(MarketPrice.timestamp))
        .where(MarketPrice.ptf_try_mwh.is_not(None))
    ).one()
    loaded = service.get_model()
    return MarketStatusResponse(
        epias_configured=epias_client.is_configured(),
        price_rows=count,
        first_price_at=first,
        last_price_at=last,
        next_delivery_date=service.next_delivery_date(),
        model=loaded[1] if loaded else None,
    )


@router.get("/ptf", response_model=list[PricePoint])
def ptf_history(
    days: int = Query(default=7, ge=1, le=366),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    return db.scalars(
        select(MarketPrice).where(MarketPrice.timestamp >= since).order_by(MarketPrice.timestamp)
    ).all()


def _forecast_response(db: Session, delivery_date: date) -> ForecastResponse:
    points = service.latest_forecast(db, delivery_date)
    hours = forecasting.delivery_hours(delivery_date)
    actual = db.scalars(
        select(MarketPrice)
        .where(MarketPrice.timestamp >= hours[0].to_pydatetime(), MarketPrice.timestamp <= hours[-1].to_pydatetime())
        .order_by(MarketPrice.timestamp)
    ).all()
    return ForecastResponse(
        delivery_date=delivery_date,
        model_version=points[0].model_version if points else None,
        issued_at=points[0].issued_at if points else None,
        points=[ForecastPoint.model_validate(p) for p in points],
        actual=[PricePoint.model_validate(a) for a in actual],
    )


@router.get("/ptf/forecast", response_model=ForecastResponse)
def get_forecast(
    delivery_date: date | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    delivery_date = delivery_date or service.next_delivery_date()
    if not service.latest_forecast(db, delivery_date):
        try:
            service.issue_forecast(db, delivery_date)
        except (service.OfferError, ValueError) as error:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))
    return _forecast_response(db, delivery_date)


@router.post("/ptf/forecast", response_model=ForecastResponse)
def reissue_forecast(
    delivery_date: date | None = None,
    user: User = Depends(require_permission(MANAGE_FINANCIAL)),
    db: Session = Depends(get_db),
):
    delivery_date = delivery_date or service.next_delivery_date()
    try:
        service.issue_forecast(db, delivery_date)
    except (service.OfferError, ValueError) as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))
    return _forecast_response(db, delivery_date)


@router.post("/sync")
async def sync(
    data: SyncRequest,
    user: User = Depends(require_permission(MANAGE_COMPANY_SETTINGS)),
    db: Session = Depends(get_db),
):
    if not epias_client.is_configured():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="EPİAŞ credentials are not configured (EPIAS_USERNAME / EPIAS_PASSWORD).",
        )
    today = pd.Timestamp.now(tz=forecasting.TR_TZ).normalize()
    # Through tomorrow: D+1 PTF is public from ~14:00 today.
    end = (today + pd.Timedelta(days=2)).tz_convert("UTC").to_pydatetime()
    start = (today - pd.Timedelta(days=data.days)).tz_convert("UTC").to_pydatetime()
    try:
        return await service.sync_market(db, start, end)
    except epias_client.EpiasAuthError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error))


# --- Factory sell offers ---


def _offer_response(db: Session, factory: Factory, delivery_date: date, notes: list[str] | None = None) -> OfferResponse:
    rows = service.list_offers(db, factory.id, delivery_date)
    sells = [r for r in rows if r.action in ("SELL", "DISCHARGE_SELL")]
    return OfferResponse(
        factory_id=factory.id,
        delivery_date=delivery_date,
        gate_closure=_gate_closure(delivery_date),
        status=rows[0].status if rows else None,
        total_quantity_mwh=round(sum(r.quantity_mwh for r in sells), 3),
        expected_revenue_try=round(sum(r.expected_revenue_try or 0 for r in rows), 2),
        revenue_p10_try=round(sum(r.revenue_p10_try or 0 for r in rows), 2),
        revenue_p90_try=round(sum(r.revenue_p90_try or 0 for r in rows), 2),
        rows=[OfferRow.model_validate(r) for r in rows],
        notes=notes or [],
    )


@offer_router.get("", response_model=OfferResponse)
def get_offer(
    delivery_date: date | None = None,
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    return _offer_response(db, factory, delivery_date or service.next_delivery_date())


@offer_router.post("", response_model=OfferResponse)
def create_offer(
    data: OfferRequest,
    factory: Factory = Depends(get_accessible_factory),
    user: User = Depends(require_permission(MANAGE_FINANCIAL)),
    db: Session = Depends(get_db),
):
    delivery_date = data.delivery_date or service.next_delivery_date()
    try:
        _, notes = service.generate_offer(db, factory, delivery_date, data.mode, data.min_price_try_mwh)
    except (service.OfferError, ValueError) as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))
    return _offer_response(db, factory, delivery_date, notes)


@offer_router.post("/mark-submitted", response_model=OfferResponse)
def mark_submitted(
    delivery_date: date,
    factory: Factory = Depends(get_accessible_factory),
    user: User = Depends(require_permission(MANAGE_FINANCIAL)),
    db: Session = Depends(get_db),
):
    """Record that the draft was submitted to the market (by the
    participant/aggregator, outside this app). Locks it against
    regeneration."""
    rows = db.scalars(
        select(SellOffer).where(
            SellOffer.factory_id == factory.id,
            SellOffer.delivery_date == delivery_date,
            SellOffer.status == "DRAFT",
        )
    ).all()
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No draft offer for this date")
    for row in rows:
        row.status = "SUBMITTED"
    db.commit()
    return _offer_response(db, factory, delivery_date)
