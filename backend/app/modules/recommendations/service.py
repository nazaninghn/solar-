from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.query_utils import utc_date
from app.forecast.service import get_energy_forecast
from app.models.battery_system import BatterySystem
from app.models.device import Device
from app.models.electricity_price import ElectricityPrice
from app.models.energy_reading import EnergyReading
from app.models.factory import Factory
from app.models.production_line import ProductionLine
from app.models.recommendation import Recommendation
from app.models.recommendation_audit_log import RecommendationAuditLog
from app.models.user import User
from app.modules.forecast.service import count_historical_days, get_factory_forecast
from app.modules.notifications.engine import evaluate_all_alert_rules, notify_recommendation
from app.modules.pricing.service import get_current_price
from app.modules.recommendations.engine import (
    RULE_STRENGTH,
    EnergyContext,
    TimeWindow,
    calculate_confidence,
    calculate_recommendation_score,
    generate_recommendations,
)
from app.modules.recommendations.scenario_engine import (
    evaluate_energy_scenarios,
    rank_scenarios,
)


def _get_historical_consumption_baseline_kwh(
    db: Session,
    factory_id: int,
    days: int = 30,
) -> float:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    day_col = utc_date(EnergyReading.timestamp).label("day")

    daily_sums = db.execute(
        select(
            day_col,
            func.sum(EnergyReading.consumption_kwh).label("total"),
        )
        .where(
            EnergyReading.factory_id == factory_id,
            EnergyReading.timestamp >= cutoff,
        )
        .group_by(day_col)
    ).all()

    if not daily_sums:
        return 0.0

    return sum(row.total for row in daily_sums) / len(daily_sums)


def _find_price_window(
    db: Session,
    factory_id: int,
    price_level: str,
) -> TimeWindow | None:
    """
    First contiguous block of upcoming stored ElectricityPrice rows at
    the given level — turns Step 10's hourly price data into an actual
    start_time/end_time window instead of a same-day guess.
    """
    now = datetime.now(timezone.utc)

    prices = db.scalars(
        select(ElectricityPrice)
        .where(
            ElectricityPrice.factory_id == factory_id,
            ElectricityPrice.timestamp >= now,
        )
        .order_by(ElectricityPrice.timestamp.asc())
    ).all()

    window_start = None
    window_end = None
    window_price = 0.0

    for price in prices:
        if price.price_level == price_level:
            if window_start is None:
                window_start = price.timestamp
                window_price = price.buy_price_per_kwh
            window_end = price.timestamp + timedelta(hours=1)
        elif window_start is not None:
            break

    if window_start is None:
        return None

    return TimeWindow(start=window_start, end=window_end, price_per_kwh=window_price)


async def _find_surplus_window(
    db: Session,
    factory: Factory,
) -> TimeWindow | None:
    """
    First contiguous block of the Step 19 hourly energy forecast where
    solar is expected to exceed consumption, paired with the sell price
    for that window from Step 10's stored prices.
    """
    try:
        forecast, _ = await get_energy_forecast(db, factory)
    except Exception:
        return None

    window_start = None
    window_end = None
    total_surplus = 0.0

    for point in forecast:
        if point["expected_balance_kwh"] > 0:
            if window_start is None:
                window_start = point["timestamp"]
            window_end = point["timestamp"] + timedelta(hours=1)
            total_surplus += point["expected_balance_kwh"]
        elif window_start is not None:
            break

    if window_start is None:
        return None

    price = db.scalar(
        select(ElectricityPrice)
        .where(
            ElectricityPrice.factory_id == factory.id,
            ElectricityPrice.timestamp >= window_start,
            ElectricityPrice.timestamp < window_end,
        )
        .order_by(ElectricityPrice.timestamp.asc())
    )
    sell_price = price.sell_price_per_kwh if price else 0.0

    return TimeWindow(
        start=window_start,
        end=window_end,
        amount_kwh=round(total_surplus, 2),
        price_per_kwh=sell_price,
    )


async def build_energy_context(db: Session, factory: Factory) -> EnergyContext:
    battery = db.scalar(
        select(BatterySystem).where(BatterySystem.factory_id == factory.id)
    )
    battery_soc = battery.state_of_charge_percent if battery else 0.0
    battery_capacity_kwh = battery.capacity_kwh if battery else 0.0
    battery_min_soc = battery.min_soc_percent if battery else 10.0
    battery_max_soc = battery.max_soc_percent if battery else 95.0

    try:
        forecast = await get_factory_forecast(db, factory)
        solar_forecast_kwh = forecast["solar"]["forecast_kwh"]
        expected_solar_reduction_percent = forecast["solar"]["reduction_percent"]
    except Exception:
        # Broadened from HTTPException-only: get_factory_forecast (Step 8)
        # never caught actual weather-provider failures (network errors,
        # non-2xx responses) — only the "no location configured" case.
        # A transient 503 from Open-Meteo shouldn't 500 the whole
        # recommendation engine; degrade to no forecast data instead,
        # same as the existing "location missing" fallback below.
        solar_forecast_kwh = 0.0
        expected_solar_reduction_percent = 0.0

    expected_consumption_kwh = _get_historical_consumption_baseline_kwh(
        db, factory.id
    )

    current_price = get_current_price(db, factory.id)
    if current_price:
        current_buy_price = current_price.buy_price_per_kwh
        current_sell_price = current_price.sell_price_per_kwh
        price_level = current_price.price_level
    else:
        current_buy_price = 0.0
        current_sell_price = 0.0
        price_level = "unknown"

    high_price_window = _find_price_window(db, factory.id, "high")
    low_price_window = _find_price_window(db, factory.id, "low")
    surplus_window = await _find_surplus_window(db, factory)

    flexible_lines = db.scalars(
        select(ProductionLine).where(
            ProductionLine.factory_id == factory.id,
            ProductionLine.flexible.is_(True),
        )
    ).all()

    return EnergyContext(
        battery_soc=battery_soc or 0.0,
        battery_capacity_kwh=battery_capacity_kwh or 0.0,
        battery_min_soc=battery_min_soc,
        battery_max_soc=battery_max_soc,
        solar_forecast_kwh=solar_forecast_kwh,
        expected_consumption_kwh=expected_consumption_kwh,
        expected_solar_reduction_percent=expected_solar_reduction_percent,
        current_buy_price=current_buy_price,
        current_sell_price=current_sell_price,
        price_level=price_level,
        high_price_window=high_price_window,
        low_price_window=low_price_window,
        surplus_window=surplus_window,
        flexible_production_lines=list(flexible_lines),
    )


def check_recommendation_safety(db: Session, factory_id: int) -> dict:
    """
    29.29-29.30: don't let a stale/broken data source produce a
    confident, "risky" recommendation. battery_error and meter_offline
    look at Device.status (16.13's IoT devices, if the factory has any
    configured) rather than BatterySystem — BatterySystem only carries
    spec/current-SOC, not a health signal. price_unavailable is read
    from the context the caller already built (price_level == "unknown"),
    not queried again here.
    """
    battery_error = (
        db.scalar(
            select(Device.id).where(
                Device.factory_id == factory_id,
                Device.device_type == "BATTERY",
                Device.status == "ERROR",
                Device.is_active.is_(True),
            )
        )
        is not None
    )

    meter_offline = (
        db.scalar(
            select(Device.id).where(
                Device.factory_id == factory_id,
                Device.device_type.in_(["FACTORY_METER", "GRID_METER"]),
                Device.status == "OFFLINE",
                Device.is_active.is_(True),
            )
        )
        is not None
    )

    return {"battery_error": battery_error, "meter_offline": meter_offline}


async def generate_factory_recommendations(
    db: Session,
    factory: Factory,
) -> list[Recommendation]:
    context = await build_energy_context(db, factory)
    items = generate_recommendations(context)

    # Step 23: replaces the three individual notify_* calls with the
    # full rule registry (adds price-spike, energy deficit/surplus,
    # financial, and system-health checks) — same EnergyContext this
    # function already built, so no extra queries for the new
    # categories that can be derived from it.
    evaluate_all_alert_rules(db, factory, context)

    weather_confidence = (
        90.0 if factory.latitude is not None and factory.longitude is not None else 50.0
    )
    data_quality = min(100.0, (count_historical_days(db, factory.id) / 7) * 100)
    confidence = calculate_confidence(weather_confidence, data_quality, RULE_STRENGTH)

    safety = check_recommendation_safety(db, factory.id)
    price_unavailable = context.price_level == "unknown"

    # 29.29: any missing/broken source knocks confidence down rather
    # than being treated as "just proceed normally" — a recommendation
    # generated on a stale price or a broken meter isn't as trustworthy
    # even for the types it doesn't outright block below.
    if safety["battery_error"] or safety["meter_offline"] or price_unavailable:
        confidence = min(confidence, 40.0)

    # 29.30, 29.7: block the specific recommendation types a broken
    # source would make actively unsafe, rather than a total blackout —
    # a battery in ERROR shouldn't get charge/discharge instructions;
    # unknown pricing shouldn't drive a buy/sell decision.
    blocked_types = set()
    if safety["battery_error"]:
        blocked_types.update({"CHARGE_BATTERY", "DISCHARGE_BATTERY"})
    if price_unavailable:
        blocked_types.update({"BUY_FROM_GRID", "SELL_TO_GRID"})

    now = datetime.now(timezone.utc)
    created = []

    for item in items:
        if item["type"] in blocked_types:
            continue

        existing = db.scalar(
            select(Recommendation).where(
                Recommendation.factory_id == factory.id,
                Recommendation.type == item["type"],
                Recommendation.status == "pending",
            )
        )

        if existing:
            continue

        start_time = item.get("start_time")
        end_time = item.get("end_time")

        hours_until_start = (
            max(0.0, (start_time - now).total_seconds() / 3600) if start_time else 1.0
        )
        score = calculate_recommendation_score(
            net_benefit=item["net_benefit"],
            confidence_percent=confidence,
            amount_kwh=item["amount_kwh"],
            expected_consumption_kwh=context.expected_consumption_kwh,
            hours_until_start=hours_until_start,
        )

        # 20.30: expires when the window it's about closes, or a flat
        # 12h out for point-in-time recommendations with no window.
        expires_at = end_time or (now + timedelta(hours=12))

        recommendation = Recommendation(
            factory_id=factory.id,
            type=item["type"],
            title=item["title"],
            description=item["description"],
            action=item["type"].lower(),
            estimated_savings=item["estimated_savings"],
            estimated_revenue=item["estimated_revenue"],
            net_benefit=item["net_benefit"],
            score=score,
            confidence=confidence,
            status="pending",
            start_time=start_time,
            end_time=end_time,
            expires_at=expires_at,
            created_at=now,
        )

        db.add(recommendation)
        db.flush()
        created.append(recommendation)

    db.commit()

    for recommendation in created:
        notify_recommendation(
            db=db,
            factory=factory,
            recommendation_id=recommendation.id,
            title=recommendation.title,
            description=recommendation.description,
        )

    return created


async def get_scenario_comparison(db: Session, factory: Factory) -> dict:
    """29.23-29.24, surfaced for explainability (29.18) — the same
    EnergyContext the rule engine already builds, run through the
    scenario comparison instead of/in addition to independent rules."""
    context = await build_energy_context(db, factory)
    imbalance_kwh = context.expected_consumption_kwh - context.solar_forecast_kwh

    scenarios = evaluate_energy_scenarios(
        context, factory.battery_degradation_cost_per_kwh
    )
    ranked = rank_scenarios(scenarios)
    optimal_name = ranked[0].name if ranked else None

    return {
        "imbalance_kwh": round(imbalance_kwh, 2),
        "scenarios": [
            {
                **scenario.__dict__,
                "is_optimal": scenario.name == optimal_name,
            }
            for scenario in scenarios
        ],
    }


def get_recommendations(db: Session, factory_id: int) -> list[Recommendation]:
    return db.scalars(
        select(Recommendation)
        .where(Recommendation.factory_id == factory_id)
        .order_by(Recommendation.score.desc().nulls_last(), Recommendation.created_at.desc())
    ).all()


def _get_owned_recommendation(
    db: Session,
    factory_id: int,
    recommendation_id: int,
) -> Recommendation:
    recommendation = db.scalar(
        select(Recommendation).where(
            Recommendation.id == recommendation_id,
            Recommendation.factory_id == factory_id,
        )
    )

    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found",
        )

    return recommendation


def get_recommendation_detail(
    db: Session,
    factory_id: int,
    recommendation_id: int,
) -> Recommendation:
    return _get_owned_recommendation(db, factory_id, recommendation_id)


def _log_audit(
    db: Session,
    recommendation_id: int,
    user_id: int,
    action: str,
    reason: str | None,
) -> None:
    db.add(
        RecommendationAuditLog(
            recommendation_id=recommendation_id,
            user_id=user_id,
            action=action,
            reason=reason,
            timestamp=datetime.now(timezone.utc),
        )
    )


def accept_recommendation(
    db: Session,
    factory_id: int,
    recommendation_id: int,
    current_user: User,
) -> Recommendation:
    recommendation = _get_owned_recommendation(db, factory_id, recommendation_id)
    recommendation.status = "accepted"
    recommendation.updated_at = datetime.now(timezone.utc)

    _log_audit(db, recommendation.id, current_user.id, "accepted", None)

    db.commit()
    db.refresh(recommendation)

    return recommendation


def reject_recommendation(
    db: Session,
    factory_id: int,
    recommendation_id: int,
    current_user: User,
    reason: str | None = None,
) -> Recommendation:
    recommendation = _get_owned_recommendation(db, factory_id, recommendation_id)
    recommendation.status = "rejected"
    recommendation.updated_at = datetime.now(timezone.utc)

    _log_audit(db, recommendation.id, current_user.id, "rejected", reason)

    db.commit()
    db.refresh(recommendation)

    return recommendation


def expire_stale_recommendations(db: Session) -> int:
    """20.30: flips PENDING recommendations past their expires_at to EXPIRED."""
    now = datetime.now(timezone.utc)

    stale = db.scalars(
        select(Recommendation).where(
            Recommendation.status == "pending",
            Recommendation.expires_at.is_not(None),
            Recommendation.expires_at < now,
        )
    ).all()

    for recommendation in stale:
        recommendation.status = "expired"
        recommendation.updated_at = now

    db.commit()

    return len(stale)
