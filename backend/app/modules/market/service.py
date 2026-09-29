"""
Market service: EPİAŞ sync -> DB, PTF forecasts, factory sell offers.
"""

import logging
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.battery_system import BatterySystem
from app.models.energy_hourly import EnergyHourly
from app.models.factory import Factory
from app.models.solar_forecast import SolarForecast
from app.modules.market import epias_client, forecasting
from app.modules.market.models import MarketFundamental, MarketPrice, PtfForecast, SellOffer
from app.modules.market.offer import BatterySpec, build_offer

logger = logging.getLogger(__name__)

MODEL_DIR = Path(settings.PTF_MODEL_DIR)
HISTORY_DAYS_FOR_FORECAST = 60
LOAD_HISTORY_DAYS = 28

_PRICE_COLS = ("ptf_try_mwh", "ptf_usd_mwh", "ptf_eur_mwh", "smf_try_mwh")
_FUND_COLS = tuple(c.name for c in MarketFundamental.__table__.columns if c.name not in ("id", "timestamp", "updated_at"))


class OfferError(ValueError):
    pass


# --- Sync ---


def _upsert(db: Session, model, rows: list[dict], columns: tuple[str, ...]) -> int:
    """Merge rows by timestamp; a column absent/None in `rows` never
    overwrites a value already stored (PTF and SMF arrive separately)."""
    merged: dict[datetime, dict] = {}
    for row in rows:
        values = {k: v for k, v in row.items() if k in columns and v is not None}
        if values:
            merged.setdefault(row["timestamp"], {}).update(values)
    if not merged:
        return 0
    now = datetime.now(timezone.utc)
    for ts, values in merged.items():
        stmt = insert(model).values(timestamp=ts, updated_at=now, **values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["timestamp"], set_={**values, "updated_at": now}
        )
        db.execute(stmt)
    db.commit()
    return len(merged)


async def sync_market(db: Session, start: datetime, end: datetime) -> dict:
    """Pull [start, end) from EPİAŞ. PTF is required; SMF and
    fundamentals are best-effort (reported, not raised) so one
    endpoint's outage never blocks price ingestion."""
    result: dict = {"start": start.isoformat(), "end": end.isoformat(), "errors": {}}
    result["ptf_rows"] = _upsert(db, MarketPrice, await epias_client.fetch_ptf(start, end), _PRICE_COLS)
    for name, fetch, model, cols in (
        ("smf", epias_client.fetch_smf, MarketPrice, _PRICE_COLS),
        ("load_plan", epias_client.fetch_load_plan, MarketFundamental, _FUND_COLS),
        ("dpp", epias_client.fetch_dpp, MarketFundamental, _FUND_COLS),
    ):
        try:
            result[f"{name}_rows"] = _upsert(db, model, await fetch(start, end), cols)
        except Exception as error:
            db.rollback()
            logger.warning("EPİAŞ %s sync failed: %s", name, error)
            result["errors"][name] = str(error)[:200]
    return result


# --- Frames ---


def load_frame(db: Session, start: datetime | None = None, end: datetime | None = None) -> pd.DataFrame:
    """Hourly UTC frame: ptf + fundamentals, the input forecasting expects."""
    q = select(MarketPrice.timestamp, MarketPrice.ptf_try_mwh)
    if start:
        q = q.where(MarketPrice.timestamp >= start)
    if end:
        q = q.where(MarketPrice.timestamp < end)
    prices = pd.DataFrame(db.execute(q).all(), columns=["timestamp", "ptf"])

    fq = select(MarketFundamental.timestamp, *[getattr(MarketFundamental, c) for c in _FUND_COLS])
    if start:
        fq = fq.where(MarketFundamental.timestamp >= start)
    if end:
        # Fundamentals may extend into the delivery day (LEP for D+1).
        fq = fq.where(MarketFundamental.timestamp < end + timedelta(days=2))
    funds = pd.DataFrame(db.execute(fq).all(), columns=["timestamp", *_FUND_COLS])

    frame = prices.set_index("timestamp") if not prices.empty else pd.DataFrame(columns=["ptf"])
    if not funds.empty:
        frame = frame.join(funds.set_index("timestamp"), how="outer")
    if not frame.empty:
        frame.index = pd.to_datetime(frame.index, utc=True)
        frame = frame.dropna(axis=1, how="all").sort_index()
        if "ptf" not in frame:
            frame["ptf"] = np.nan
    return frame


# --- Forecasts ---


def get_model():
    return forecasting.load(MODEL_DIR)


def issue_forecast(db: Session, delivery_date: date) -> list[PtfForecast]:
    """Forecast `delivery_date` using only data a bidder had on the day
    before; upserts one row per hour for the model version used."""
    cutoff = forecasting.delivery_hours(delivery_date)[0]
    frame = load_frame(db, start=cutoff - timedelta(days=HISTORY_DAYS_FOR_FORECAST), end=cutoff)
    if frame.empty or frame["ptf"].dropna().empty:
        raise OfferError("No PTF history in the database yet — run a market sync first.")

    loaded = get_model()
    if loaded is not None:
        model, meta = loaded
        prices = forecasting.predict(model, frame, delivery_date)
        version = meta["version"]
    else:
        prices = forecasting.baseline_forecast(frame, delivery_date)
        version = forecasting.BASELINE_VERSION

    now = datetime.now(timezone.utc)
    for ts, row in prices.iterrows():
        values = dict(
            delivery_date=delivery_date,
            p10_try_mwh=round(float(row["p10"]), 2),
            p50_try_mwh=round(float(row["p50"]), 2),
            p90_try_mwh=round(float(row["p90"]), 2),
            issued_at=now,
        )
        stmt = insert(PtfForecast).values(timestamp=ts.to_pydatetime(), model_version=version, **values)
        db.execute(stmt.on_conflict_do_update(constraint="uq_ptf_forecast_hour_model", set_=values))
    db.commit()
    return latest_forecast(db, delivery_date)


def latest_forecast(db: Session, delivery_date: date) -> list[PtfForecast]:
    """Most recently issued forecast for the date (whichever model)."""
    rows = db.scalars(
        select(PtfForecast)
        .where(PtfForecast.delivery_date == delivery_date)
        .order_by(PtfForecast.issued_at.desc())
    ).all()
    if not rows:
        return []
    newest = rows[0].issued_at
    return sorted([r for r in rows if r.issued_at == newest], key=lambda r: r.timestamp)


# --- Offers ---


def _expected_load(db: Session, factory_id: int, hours: pd.DatetimeIndex) -> np.ndarray:
    """Mean consumption for the same local hour and day type (weekday /
    weekend or holiday) over the last LOAD_HISTORY_DAYS days."""
    since = hours[0] - timedelta(days=LOAD_HISTORY_DAYS)
    rows = db.execute(
        select(EnergyHourly.hour, EnergyHourly.consumption_kwh).where(
            EnergyHourly.factory_id == factory_id,
            EnergyHourly.hour >= since,
            EnergyHourly.hour < hours[0],
        )
    ).all()
    if len(rows) < 24 * 7:
        raise OfferError(
            "Less than a week of hourly consumption history — can't estimate how much PV the factory will use itself."
        )
    hist = pd.DataFrame(rows, columns=["hour", "kwh"])
    local = pd.to_datetime(hist["hour"], utc=True).dt.tz_convert(forecasting.TR_TZ)
    hist["h"] = local.dt.hour
    hist["off"] = [
        int(ts.dayofweek >= 5 or ts.date() in forecasting._TR_HOLIDAYS) for ts in local
    ]
    profile = hist.groupby(["off", "h"])["kwh"].mean()
    fallback = hist.groupby("h")["kwh"].mean()

    out = []
    for ts in hours.tz_convert(forecasting.TR_TZ):
        off = int(ts.dayofweek >= 5 or ts.date() in forecasting._TR_HOLIDAYS)
        out.append(profile.get((off, ts.hour), fallback.get(ts.hour, 0.0)))
    return np.array(out, dtype=float)


def _expected_pv(db: Session, factory_id: int, hours: pd.DatetimeIndex) -> np.ndarray:
    rows = db.execute(
        select(SolarForecast.timestamp, SolarForecast.expected_energy_kwh).where(
            SolarForecast.factory_id == factory_id,
            SolarForecast.timestamp >= hours[0].to_pydatetime(),
            SolarForecast.timestamp <= hours[-1].to_pydatetime(),
        )
    ).all()
    by_ts = {pd.Timestamp(ts).tz_convert("UTC"): kwh for ts, kwh in rows}
    if not by_ts:
        raise OfferError("No solar forecast for this date — the solar forecast job must run first.")
    return np.array([by_ts.get(ts, 0.0) for ts in hours], dtype=float)


def _battery_spec(db: Session, factory: Factory) -> BatterySpec | None:
    battery = db.scalar(select(BatterySystem).where(BatterySystem.factory_id == factory.id))
    if battery is None:
        return None
    usable = battery.usable_capacity_kwh or battery.capacity_kwh * (
        (battery.max_soc_percent - battery.min_soc_percent) / 100.0
    )
    if battery.state_of_health_percent:
        usable *= battery.state_of_health_percent / 100.0
    # Degradation cost only when it's already in TL — mixing a USD
    # figure into TL prices would silently distort every bid.
    degradation = (
        factory.battery_degradation_cost_per_kwh
        if factory.currency == "TRY" and factory.battery_degradation_cost_per_kwh
        else 0.0
    )
    return BatterySpec(
        usable_kwh=usable,
        charge_kw=battery.charge_rate_kw or usable / 2,
        discharge_kw=battery.discharge_rate_kw or usable / 2,
        efficiency=(battery.efficiency_percent or 90.0) / 100.0,
        degradation_try_per_kwh=degradation,
    )


def generate_offer(
    db: Session,
    factory: Factory,
    delivery_date: date,
    mode: str = "GOP_BID",
    min_price: float = 0.0,
) -> tuple[list[SellOffer], list[str]]:
    submitted = db.scalar(
        select(SellOffer.id).where(
            SellOffer.factory_id == factory.id,
            SellOffer.delivery_date == delivery_date,
            SellOffer.status == "SUBMITTED",
        )
    )
    if submitted:
        raise OfferError("An offer for this date was already marked submitted; it can't be regenerated.")

    forecast = latest_forecast(db, delivery_date) or issue_forecast(db, delivery_date)
    hours = forecasting.delivery_hours(delivery_date)
    ptf = pd.DataFrame(
        {
            "p10": [f.p10_try_mwh for f in forecast],
            "p50": [f.p50_try_mwh for f in forecast],
            "p90": [f.p90_try_mwh for f in forecast],
        },
        index=hours,
    )
    pv = _expected_pv(db, factory.id, hours)
    load = _expected_load(db, factory.id, hours)
    battery = _battery_spec(db, factory)

    plan = build_offer(hours, pv, load, ptf, mode=mode, min_price=min_price, battery=battery)

    db.execute(delete(SellOffer).where(
        SellOffer.factory_id == factory.id,
        SellOffer.delivery_date == delivery_date,
        SellOffer.status == "DRAFT",
    ))
    now = datetime.now(timezone.utc)
    rows = [
        SellOffer(
            factory_id=factory.id,
            delivery_date=delivery_date,
            timestamp=h.timestamp.to_pydatetime(),
            tier=h.tier,
            mode=mode,
            action=h.action,
            quantity_mwh=h.quantity_mwh,
            price_try_mwh=h.price_try_mwh,
            expected_ptf_try_mwh=h.expected_ptf,
            expected_revenue_try=h.revenue_p50,
            revenue_p10_try=h.revenue_p10,
            revenue_p90_try=h.revenue_p90,
            status="DRAFT",
            inputs={**h.inputs, "forecast_model": forecast[0].model_version},
            created_at=now,
        )
        for h in plan.hours
    ]
    db.add_all(rows)
    db.commit()
    return list_offers(db, factory.id, delivery_date), plan.notes


def list_offers(db: Session, factory_id: int, delivery_date: date) -> list[SellOffer]:
    return db.scalars(
        select(SellOffer)
        .where(SellOffer.factory_id == factory_id, SellOffer.delivery_date == delivery_date)
        .order_by(SellOffer.timestamp, SellOffer.tier)
    ).all()


def next_delivery_date(now: datetime | None = None) -> date:
    """The date bids are being prepared for right now: tomorrow (TR)."""
    now = now or datetime.now(timezone.utc)
    return (pd.Timestamp(now).tz_convert(forecasting.TR_TZ) + pd.Timedelta(days=1)).date()
