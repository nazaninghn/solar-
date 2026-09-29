"""
Failure prediction: assess devices, persist, alert.

Per device:
  1. load the last WINDOW_HOURS of telemetry, resample to one minute
  2. rule indicators for its type (+ comms indicators for every type)
  3. inverters only: the PV ML model, when irradiance and daylight allow
  4. trend projection from this device's own assessment history
  5. combine -> FailureRiskAssessment row; HIGH/CRITICAL -> notification,
     dropping back below HIGH auto-resolves it
"""

import logging
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.battery_system import BatterySystem
from app.models.device import Device
from app.models.device_energy_reading import DeviceEnergyReading
from app.models.factory import Factory
from app.models.solar_system import SolarSystem
from app.modules.failure_prediction import indicators as ind
from app.modules.failure_prediction.mapping import (
    ReadingPoint,
    WeatherSample,
    raw_value,
    build_frame,
)
from app.modules.failure_prediction.ml_model import get_model
from app.modules.failure_prediction.models import FailureRiskAssessment
from app.modules.failure_prediction.scoring import combine, ml_indicator
from app.modules.notifications.engine import _auto_resolve_if_active
from app.modules.notifications.service import create_notification

logger = logging.getLogger(__name__)

WINDOW_HOURS = 24
# The ML model only needs the recent past (30 warm-up minutes + a few
# 15-minute bins); feeding it the whole day just costs time.
ML_WINDOW_HOURS = 6
TREND_DAYS = 30
ALERT_LEVELS = {"HIGH", "CRITICAL"}
ALERT_COOLDOWN_MINUTES = 240


async def fetch_weather(factory: Factory) -> list[WeatherSample] | None:
    """Today's hourly irradiance/temperature from Open-Meteo (its
    forecast starts at today's 00:00 UTC, so it covers the hours that
    already passed). None on any failure — ML just skips, rules still run."""
    if factory.latitude is None or factory.longitude is None:
        return None
    try:
        from app.weather.providers.open_meteo_provider import OpenMeteoProvider
        from app.weather.service import WeatherService

        points = await WeatherService(OpenMeteoProvider()).get_forecast(
            latitude=factory.latitude, longitude=factory.longitude, days=1
        )
    except Exception as error:
        logger.warning("failure_prediction: weather fetch failed for factory %s: %s", factory.id, error)
        return None
    return [
        WeatherSample(p.timestamp, p.solar_irradiance_w_m2, p.temperature_c) for p in points
    ]


def _load_readings(db: Session, device_id: int, since: datetime) -> list[DeviceEnergyReading]:
    return db.scalars(
        select(DeviceEnergyReading)
        .where(DeviceEnergyReading.device_id == device_id, DeviceEnergyReading.timestamp >= since)
        .order_by(DeviceEnergyReading.timestamp.asc())
    ).all()


def _minute_frame(readings: list[DeviceEnergyReading], weather: list[WeatherSample] | None) -> pd.DataFrame:
    """One-minute means of the numeric telemetry, used by the rule
    indicators. Irradiance: device raw_data first, else weather."""
    cols = ["power_kw", "voltage", "frequency", "temperature_c", "soc_percent", "irradiance"]
    if not readings:
        return pd.DataFrame(columns=cols)
    df = pd.DataFrame(
        {
            "timestamp": pd.to_datetime([r.timestamp for r in readings], utc=True),
            "power_kw": [r.power_kw for r in readings],
            "voltage": [r.voltage for r in readings],
            "frequency": [r.frequency for r in readings],
            "temperature_c": [r.temperature_c for r in readings],
            "soc_percent": [r.soc_percent for r in readings],
            "irradiance": [raw_value(r.raw_data, "irradiance") for r in readings],
        }
    ).astype({c: float for c in cols})
    minute = df.set_index("timestamp").resample("1min").mean().dropna(how="all")

    if minute["irradiance"].isna().all() and weather:
        w = (
            pd.DataFrame(
                {
                    "timestamp": pd.to_datetime([x.timestamp for x in weather], utc=True),
                    "irradiance": [x.irradiance_w_m2 for x in weather],
                }
            )
            .astype({"irradiance": float})
            .set_index("timestamp")
            .sort_index()
        )
        union = w.index.union(minute.index)
        minute["irradiance"] = w.reindex(union).interpolate(method="time").reindex(minute.index)["irradiance"]
    return minute


def _inverter_rating_kw(db: Session, device: Device, factory: Factory, readings) -> float | None:
    """Device-reported rating first; otherwise the factory's installed PV
    capacity split evenly over its active inverters."""
    for reading in reversed(readings):
        raw = reading.raw_data or {}
        for key in ("rated_power_kw", "nominal_power_kw"):
            if isinstance(raw.get(key), (int, float)) and raw[key] > 0:
                return float(raw[key])
    solar = db.scalar(select(SolarSystem).where(SolarSystem.factory_id == factory.id))
    capacity = (solar.installed_capacity_kw if solar else None) or factory.solar_capacity_kw
    if not capacity:
        return None
    inverters = db.scalar(
        select(func.count(Device.id)).where(
            Device.factory_id == factory.id,
            Device.device_type == "INVERTER",
            Device.is_active.is_(True),
        )
    ) or 1
    return float(capacity) / inverters


def _history(db: Session, device_id: int, code: str, now: datetime) -> list[tuple[pd.Timestamp, float]]:
    rows = db.execute(
        select(FailureRiskAssessment.assessed_at, FailureRiskAssessment.indicators).where(
            FailureRiskAssessment.device_id == device_id,
            FailureRiskAssessment.assessed_at >= now - timedelta(days=TREND_DAYS),
        )
    ).all()
    out = []
    for assessed_at, indicators in rows:
        for item in indicators or []:
            if item.get("code") == code and item.get("value") is not None:
                out.append((pd.Timestamp(assessed_at), float(item["value"])))
    return out


def _run_ml(readings, rated_kw, factory, weather, now) -> tuple[str, object | None, object | None]:
    if rated_kw is None:
        return "NO_CAPACITY", None, None
    recent = [r for r in readings if r.timestamp >= now - timedelta(hours=ML_WINDOW_HOURS)]
    points = [
        ReadingPoint(r.timestamp, r.power_kw, r.voltage, r.temperature_c, r.raw_data)
        for r in recent
        if r.data_quality not in ("INVALID",)
    ]
    if not points:
        return "INSUFFICIENT_DATA", None, None
    model = get_model()
    mapped = build_frame(points, rated_kw, model.meta, weather, local_tz=factory.timezone or "UTC")
    if mapped is None:
        has_irr = any(raw_value(p.raw_data, "irradiance") is not None for p in points) or bool(weather)
        return ("NOT_DAYLIGHT" if has_irr else "NO_IRRADIANCE"), None, None
    prediction = model.predict(mapped.frame)
    if prediction is None:
        return "NOT_DAYLIGHT", None, mapped
    return "OK", prediction, mapped


def assess_device(
    db: Session,
    device: Device,
    factory: Factory,
    weather: list[WeatherSample] | None = None,
    now: datetime | None = None,
    notify: bool = True,
) -> FailureRiskAssessment:
    now = now or datetime.now(timezone.utc)
    readings = _load_readings(db, device.id, now - timedelta(hours=WINDOW_HOURS))
    minute = _minute_frame(readings, weather)

    indicators: list[ind.Indicator] = ind.comms_indicators(
        device,
        pd.Series([r.timestamp for r in readings]),
        pd.Series([r.data_quality for r in readings]),
        WINDOW_HOURS,
    )

    ml_status, prediction, mapped = "NOT_APPLICABLE", None, None
    days_to_threshold = None

    if device.device_type == "INVERTER":
        rated_kw = _inverter_rating_kw(db, device, factory, readings)
        indicators += ind.inverter_indicators(minute, rated_kw or 0.0)
        ml_status, prediction, mapped = _run_ml(readings, rated_kw, factory, weather, now)
        if prediction is not None:
            indicators.append(ml_indicator(prediction.failure_probability, prediction.threshold, prediction.fault_type))
        days_to_threshold = ind.days_to_threshold(
            _history(db, device.id, "performance_ratio", now), ind.PR_WARN
        )
    elif device.device_type == "BATTERY":
        battery = db.scalar(select(BatterySystem).where(BatterySystem.factory_id == factory.id))
        indicators += ind.battery_indicators(minute, battery)
        days_to_threshold = ind.days_to_threshold(
            _history(db, device.id, "state_of_health", now), ind.SOH_CRITICAL
        )
    else:
        indicators += ind.meter_indicators(minute)

    score, level, top, action = combine(indicators)

    assessment = FailureRiskAssessment(
        factory_id=factory.id,
        device_id=device.id,
        assessed_at=now,
        device_type=device.device_type,
        risk_score=score,
        risk_level=level,
        method="ML+RULES" if prediction is not None else "RULES",
        ml_status=ml_status,
        model_version=prediction.model_version if prediction else None,
        failure_probability=prediction.failure_probability if prediction else None,
        horizon_minutes=prediction.horizon_minutes if prediction else None,
        fault_type=prediction.fault_type if prediction else None,
        fault_type_confidence=prediction.fault_type_confidence if prediction else None,
        irradiance_source=mapped.irradiance_source if mapped else None,
        imputed_inputs=mapped.imputed if mapped else None,
        indicators=[i.to_dict() for i in indicators],
        top_reason=top.code if top else None,
        recommended_action=action,
        days_to_threshold=days_to_threshold,
        data_points=len(readings),
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    if notify:
        _notify(db, factory, device, assessment, top)
    return assessment


def _notify(db: Session, factory: Factory, device: Device, assessment: FailureRiskAssessment, top) -> None:
    # One rule_id per device, so one device's alert never suppresses
    # (via cooldown) or resolves another's.
    rule = SimpleNamespace(rule_id=f"FAILURE_RISK:{device.id}", cooldown_minutes=ALERT_COOLDOWN_MINUTES)
    if assessment.risk_level not in ALERT_LEVELS:
        _auto_resolve_if_active(db, factory, "DEVICE", rule)
        return
    create_notification(
        db=db,
        factory_id=factory.id,
        notification_type="DEVICE",
        severity="CRITICAL" if assessment.risk_level == "CRITICAL" else "WARNING",
        title=f"Failure risk {assessment.risk_level.lower()}: {device.name}",
        message=(top.message if top else "") + (
            f" {assessment.recommended_action}" if assessment.recommended_action else ""
        ),
        rule_id=rule.rule_id,
        cooldown_minutes=rule.cooldown_minutes,
        value=assessment.risk_score,
        threshold=50.0,
        unit="risk",
        source="FAILURE_PREDICTION",
        alert_metadata={
            "related_resource": "maintenance",
            "deep_link": "/dashboard/maintenance",
            "device_id": device.id,
            "assessment_id": assessment.id,
        },
    )


def assess_factory(
    db: Session,
    factory: Factory,
    weather: list[WeatherSample] | None = None,
    notify: bool = True,
) -> list[FailureRiskAssessment]:
    devices = db.scalars(
        select(Device).where(Device.factory_id == factory.id, Device.is_active.is_(True)).order_by(Device.id)
    ).all()
    now = datetime.now(timezone.utc)
    return [assess_device(db, d, factory, weather, now=now, notify=notify) for d in devices]


def latest_assessments(db: Session, factory_id: int) -> list[tuple[Device, FailureRiskAssessment | None]]:
    latest = (
        select(
            FailureRiskAssessment.device_id,
            func.max(FailureRiskAssessment.assessed_at).label("latest"),
        )
        .where(FailureRiskAssessment.factory_id == factory_id)
        .group_by(FailureRiskAssessment.device_id)
        .subquery()
    )
    rows = db.scalars(
        select(FailureRiskAssessment).join(
            latest,
            (FailureRiskAssessment.device_id == latest.c.device_id)
            & (FailureRiskAssessment.assessed_at == latest.c.latest),
        )
    ).all()
    by_device = {r.device_id: r for r in rows}
    devices = db.scalars(
        select(Device).where(Device.factory_id == factory_id, Device.is_active.is_(True)).order_by(Device.id)
    ).all()
    return [(d, by_device.get(d.id)) for d in devices]
