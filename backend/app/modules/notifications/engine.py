from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.device import Device
from app.models.electricity_price import ElectricityPrice
from app.models.factory import Factory
from app.models.financial_record import FinancialRecord
from app.models.job_run import JobRun
from app.notifications.rules import (
    BatteryLowRule,
    BatteryRuleContext,
    EnergyBalanceRule,
    EnergyBalanceRuleContext,
    EnergyDeficitRule,
    EnergyRuleContext,
    EnergySurplusRule,
    FinancialRuleContext,
    FinancialSavingsRule,
    FinancialSpikeRule,
    PriceHighRule,
    PriceRuleContext,
    PriceSpikeRule,
    WeatherForecastRule,
    WeatherRuleContext,
    SystemHealthRule,
    SystemRuleContext,
)
from app.modules.notifications.service import create_notification


def _create_from_rule(
    db: Session,
    factory: Factory,
    alert_type: str,
    rule,
    result: dict | None,
) -> None:
    if result is None:
        return

    create_notification(
        db=db,
        factory_id=factory.id,
        notification_type=alert_type,
        severity=result["severity"],
        title=result["title"],
        message=result["message"],
        rule_id=rule.rule_id,
        cooldown_minutes=rule.cooldown_minutes,
        value=result.get("value"),
        threshold=result.get("threshold"),
        unit=result.get("unit"),
        source=alert_type,
        alert_metadata=result.get("alert_metadata"),
    )


# --- Existing call sites (Step 14) — signatures unchanged so
# app/modules/recommendations/service.py doesn't need to change, but
# internally now routed through the rules registry with cooldown-based
# dedup instead of the old date-scoped deduplication_key. ---


def notify_battery_low(db: Session, factory: Factory, battery_percentage: float) -> None:
    rule = BatteryLowRule()
    result = rule.evaluate(BatteryRuleContext(soc_percent=battery_percentage))
    _create_from_rule(db, factory, "BATTERY", rule, result)


def notify_low_solar_forecast(
    db: Session, factory: Factory, decrease_percent: float
) -> None:
    rule = WeatherForecastRule()
    result = rule.evaluate(WeatherRuleContext(solar_reduction_percent=decrease_percent))
    _create_from_rule(db, factory, "FORECAST", rule, result)


def notify_high_electricity_price(
    db: Session, factory: Factory, price_level: str, buy_price: float
) -> None:
    rule = PriceHighRule()
    result = rule.evaluate(
        PriceRuleContext(
            current_price=buy_price, average_price_24h=0, price_level=price_level
        )
    )
    _create_from_rule(db, factory, "PRICE", rule, result)


def notify_recommendation(
    db: Session,
    factory: Factory,
    recommendation_id: int,
    title: str,
    description: str,
) -> None:
    create_notification(
        db=db,
        factory_id=factory.id,
        notification_type="RECOMMENDATION",
        severity="INFO",
        title=title,
        message=description,
        deduplication_key=f"factory-{factory.id}-recommendation-{recommendation_id}",
        source="RECOMMENDATION_ENGINE",
        alert_metadata={
            "recommended_action": None,
            "related_resource": "recommendation",
            "related_resource_id": recommendation_id,
        },
    )


# --- New categories (Step 23) ---


def notify_price_spike(
    db: Session, factory: Factory, current_price: float, average_price_24h: float
) -> None:
    rule = PriceSpikeRule()
    result = rule.evaluate(
        PriceRuleContext(
            current_price=current_price,
            average_price_24h=average_price_24h,
            price_level="",
        )
    )
    _create_from_rule(db, factory, "PRICE", rule, result)


def notify_energy_balance(
    db: Session,
    factory: Factory,
    forecast_consumption_kwh: float,
    forecast_solar_kwh: float,
    available_battery_kwh: float,
) -> None:
    context = EnergyRuleContext(
        forecast_consumption_kwh=forecast_consumption_kwh,
        forecast_solar_kwh=forecast_solar_kwh,
        available_battery_kwh=available_battery_kwh,
    )

    deficit_rule = EnergyDeficitRule()
    _create_from_rule(db, factory, "ENERGY", deficit_rule, deficit_rule.evaluate(context))

    surplus_rule = EnergySurplusRule()
    _create_from_rule(
        db, factory, "ENERGY", surplus_rule, surplus_rule.evaluate(context)
    )


def notify_financial_status(
    db: Session, factory: Factory, today_cost: float, average_30d_cost: float
) -> None:
    context = FinancialRuleContext(
        today_cost=today_cost, average_30d_cost=average_30d_cost
    )

    spike_rule = FinancialSpikeRule()
    _create_from_rule(db, factory, "FINANCIAL", spike_rule, spike_rule.evaluate(context))

    savings_rule = FinancialSavingsRule()
    _create_from_rule(
        db, factory, "FINANCIAL", savings_rule, savings_rule.evaluate(context)
    )


def notify_system_health(
    db: Session, factory: Factory, offline_devices: list, recent_job_failures: list
) -> None:
    rule = SystemHealthRule()
    result = rule.evaluate(
        SystemRuleContext(
            offline_devices=offline_devices, recent_job_failures=recent_job_failures
        )
    )
    _create_from_rule(db, factory, "SYSTEM", rule, result)


def notify_energy_balance_error(
    db: Session,
    factory: Factory,
    diff_kwh: float,
    supply_kwh: float,
    demand_kwh: float,
    tolerance_kwh: float,
) -> None:
    rule = EnergyBalanceRule()
    result = rule.evaluate(
        EnergyBalanceRuleContext(
            diff_kwh=diff_kwh,
            supply_kwh=supply_kwh,
            demand_kwh=demand_kwh,
            tolerance_kwh=tolerance_kwh,
        )
    )
    _create_from_rule(db, factory, "ENERGY", rule, result)


def evaluate_all_alert_rules(db: Session, factory: Factory, context) -> None:
    """
    23.9's periodic check, reusing the same EnergyContext the
    recommendation engine (Step 11/20) already builds every hour rather
    than re-fetching battery/price/forecast data a second time.
    """
    notify_battery_low(db, factory, context.battery_soc)
    notify_low_solar_forecast(db, factory, context.expected_solar_reduction_percent)
    notify_high_electricity_price(
        db, factory, context.price_level, context.current_buy_price
    )

    average_price_24h = _get_average_price_24h(db, factory.id)
    notify_price_spike(db, factory, context.current_buy_price, average_price_24h)

    available_battery_kwh = context.battery_capacity_kwh * (
        context.battery_soc / 100
    )
    notify_energy_balance(
        db,
        factory,
        forecast_consumption_kwh=context.expected_consumption_kwh,
        forecast_solar_kwh=context.solar_forecast_kwh,
        available_battery_kwh=available_battery_kwh,
    )

    today_cost, average_30d_cost = _get_financial_costs(db, factory.id)
    notify_financial_status(db, factory, today_cost, average_30d_cost)

    offline_devices = _get_offline_devices(db, factory.id)
    recent_job_failures = _get_recent_job_failures(db)
    notify_system_health(db, factory, offline_devices, recent_job_failures)


def _get_average_price_24h(db: Session, factory_id: int) -> float:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

    return db.scalar(
        select(func.coalesce(func.avg(ElectricityPrice.buy_price_per_kwh), 0)).where(
            ElectricityPrice.factory_id == factory_id,
            ElectricityPrice.timestamp >= cutoff,
        )
    ) or 0.0


def _get_financial_costs(db: Session, factory_id: int) -> tuple[float, float]:
    today = datetime.now(timezone.utc).date()
    thirty_days_ago = today - timedelta(days=30)

    today_record = db.scalar(
        select(FinancialRecord).where(
            FinancialRecord.factory_id == factory_id, FinancialRecord.date == today
        )
    )
    today_cost = today_record.grid_purchase_cost if today_record else 0.0

    average_30d = db.scalar(
        select(func.coalesce(func.avg(FinancialRecord.grid_purchase_cost), 0)).where(
            FinancialRecord.factory_id == factory_id,
            FinancialRecord.date >= thirty_days_ago,
            FinancialRecord.date < today,
        )
    ) or 0.0

    return today_cost, average_30d


def _get_offline_devices(db: Session, factory_id: int, stale_minutes: int = 15) -> list:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=stale_minutes)

    return db.scalars(
        select(Device).where(
            Device.factory_id == factory_id,
            Device.is_active.is_(True),
            (Device.last_seen_at.is_(None)) | (Device.last_seen_at < cutoff),
        )
    ).all()


def _get_recent_job_failures(db: Session, minutes: int = 60) -> list:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    return db.scalars(
        select(JobRun).where(
            JobRun.status == "failed",
            JobRun.started_at >= cutoff,
        )
    ).all()
