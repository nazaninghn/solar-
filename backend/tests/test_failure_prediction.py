import math
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database.session import SessionLocal
from app.main import app
from app.models.device import Device
from app.models.device_energy_reading import DeviceEnergyReading
from app.models.notification import Notification
from app.modules.failure_prediction import indicators as ind
from app.modules.failure_prediction.features import build_features
from app.modules.failure_prediction.mapping import ReadingPoint, WeatherSample, build_frame
from app.modules.failure_prediction.ml_model import get_model
from app.modules.failure_prediction.scoring import ML_MAX_SCORE, combine, level_for, ml_indicator

client = TestClient(app)

OYA_DIR = Path(os.environ.get("OYA_PROJECT_DIR", "D:/OYA-PROJECT"))


def _synthetic_day(
    start: datetime,
    hours: float,
    rated_kw: float = 500.0,
    pr: float = 0.82,
    step_s: int = 30,
    with_irradiance: bool = True,
    seed: int = 0,
) -> list[ReadingPoint]:
    """Clear-sky day: irradiance a half-sine peaking at 12:00 of `start`'s
    clock, output = rated * irradiance/1000 * pr, small noise."""
    rng = np.random.default_rng(seed)
    points = []
    for i in range(int(hours * 3600 / step_s)):
        ts = start + timedelta(seconds=i * step_s)
        h = ts.hour + ts.minute / 60
        irr = max(0.0, 1000 * math.sin(math.pi * (h - 5.5) / 14)) * (1 + 0.02 * rng.standard_normal())
        power = max(0.0, rated_kw * irr / 1000 * pr * (1 + 0.01 * rng.standard_normal()))
        points.append(ReadingPoint(
            timestamp=ts,
            power_kw=power,
            voltage=400 + 2 * rng.standard_normal(),
            temperature_c=35 + irr / 50,
            raw_data={"irradiance_w_m2": irr} if with_irradiance else None,
        ))
    return points


# --- Feature parity with the thesis pipeline ---


@pytest.mark.skipif(
    not (OYA_DIR / "data" / "processed" / "features.csv").exists(),
    reason="OYA-PROJECT data not available locally",
)
def test_features_match_thesis_pipeline():
    """The models expect 1-minute features averaged into 15-minute bins;
    rebuilding them from the thesis's own 1-minute data must reproduce
    its features.csv (and therefore identical model outputs)."""
    meta = get_model().meta
    sensors = list(meta["training_medians"])
    clean = pd.read_csv(OYA_DIR / "data/processed/merged_clean.csv", parse_dates=["measured_on"])
    clean = clean.tail(6000)
    ref = pd.read_csv(OYA_DIR / "data/processed/features.csv", parse_dates=["measured_on"]).tail(400)

    ours = (
        build_features(clean[["measured_on", *sensors]])
        .set_index("measured_on")
        .resample("15min")
        .mean()
        .dropna(subset=["ac_power__423"])
        .reset_index()
    )
    merged = ours.merge(ref, on="measured_on", suffixes=("_o", "_r")).iloc[40:]
    assert len(merged) > 100

    cols = meta["binary"]["features"]
    model = get_model()
    import xgboost as xgb

    p_ours = model._binary.predict(xgb.DMatrix(merged[[c + "_o" for c in cols]].to_numpy(np.float32)))
    p_ref = model._binary.predict(xgb.DMatrix(merged[[c + "_r" for c in cols]].to_numpy(np.float32)))
    # Rolling std of near-constant power differs in float rounding
    # (catastrophic cancellation), which can nudge an occasional bin by
    # <1e-3; everything else must be identical.
    diff = np.abs(p_ours - p_ref)
    assert diff.max() < 2e-3
    assert (diff < 1e-6).mean() > 0.95


# --- Mapping ---


def test_build_frame_scales_power_to_reference_system():
    meta = get_model().meta
    start = datetime(2026, 6, 15, 9, 0, tzinfo=timezone.utc)
    mapped = build_frame(_synthetic_day(start, 1), 500.0, meta)

    assert mapped is not None
    assert mapped.scale == pytest.approx(meta["reference"]["ac_power_w"] / 500_000)
    # 400 V nominal -> reference 120 V-class level, per-unit preserved
    assert mapped.frame["ac_voltage__426"].median() == pytest.approx(meta["reference"]["ac_voltage_v"], rel=0.02)
    assert "dc_power" in mapped.imputed and "inverter_temp" not in mapped.imputed
    assert mapped.irradiance_source == "device"


def test_build_frame_without_any_irradiance_returns_none():
    start = datetime(2026, 6, 15, 9, 0, tzinfo=timezone.utc)
    points = _synthetic_day(start, 1, with_irradiance=False)
    assert build_frame(points, 500.0, get_model().meta) is None


def test_build_frame_falls_back_to_weather_irradiance():
    start = datetime(2026, 6, 15, 9, 0, tzinfo=timezone.utc)
    points = _synthetic_day(start, 1, with_irradiance=False)
    weather = [
        WeatherSample(start + timedelta(hours=h), 700.0, 25.0) for h in range(-1, 3)
    ]
    mapped = build_frame(points, 500.0, get_model().meta, weather)
    assert mapped is not None
    assert mapped.irradiance_source == "weather"
    assert mapped.frame["poa_irradiance__421"].median() == pytest.approx(700.0)


# --- Model ---


def test_model_scores_daylight_and_skips_night():
    model = get_model()
    day = build_frame(_synthetic_day(datetime(2026, 6, 15, 6, 0, tzinfo=timezone.utc), 5), 500.0, model.meta)
    prediction = model.predict(day.frame)
    assert prediction is not None
    assert 0.0 <= prediction.failure_probability <= 1.0
    assert prediction.horizon_minutes == 180

    dusk = build_frame(_synthetic_day(datetime(2026, 6, 15, 18, 30, tzinfo=timezone.utc), 1.5), 500.0, model.meta)
    assert dusk is None or model.predict(dusk.frame) is None


# --- Indicators ---


def _minute_df(points: list[ReadingPoint]) -> pd.DataFrame:
    return pd.DataFrame({
        "power_kw": [p.power_kw for p in points],
        "voltage": [p.voltage for p in points],
        "frequency": [50.0] * len(points),
        "temperature_c": [p.temperature_c for p in points],
        "soc_percent": [np.nan] * len(points),
        "irradiance": [p.raw_data["irradiance_w_m2"] for p in points],
    }, index=pd.to_datetime([p.timestamp for p in points], utc=True))


def test_performance_ratio_flags_underperforming_array():
    start = datetime(2026, 6, 15, 8, 0, tzinfo=timezone.utc)
    healthy = ind.inverter_indicators(_minute_df(_synthetic_day(start, 4, step_s=60)), 500.0)
    degraded = ind.inverter_indicators(_minute_df(_synthetic_day(start, 4, pr=0.45, step_s=60)), 500.0)

    pr_ok = next(i for i in healthy if i.code == "performance_ratio")
    pr_bad = next(i for i in degraded if i.code == "performance_ratio")
    assert pr_ok.value == pytest.approx(0.82, abs=0.03) and pr_ok.score == 0
    assert pr_bad.score == 90


def test_battery_indicators_use_battery_specs():
    battery = type("B", (), {
        "state_of_health_percent": 72.0, "temperature_c": 30.0,
        "efficiency_percent": 92.0, "cycle_count": 1000, "min_soc_percent": 10.0,
    })()
    result = {i.code: i for i in ind.battery_indicators(pd.DataFrame(), battery)}
    assert result["state_of_health"].score > 70
    assert result["battery_temperature"].score == 0
    assert result["round_trip_efficiency"].score == 0


def test_comms_indicators_count_gaps():
    device = type("D", (), {
        "consecutive_error_count": 0, "last_error_message": None,
        "status": "ONLINE", "is_active": True,
    })()
    base = pd.Timestamp("2026-06-15T08:00Z")
    ts = pd.Series([base, base + pd.Timedelta(minutes=1), base + pd.Timedelta(minutes=40), base + pd.Timedelta(minutes=41)])
    result = {i.code: i for i in ind.comms_indicators(device, ts, pd.Series(["GOOD"] * 4), 24)}
    assert result["data_gaps"].value == 1
    assert result["data_quality"].score == 0


def test_days_to_threshold_projects_declining_trend():
    start = pd.Timestamp("2026-06-01T12:00Z")
    history = [(start + pd.Timedelta(days=d), 0.85 - 0.005 * d) for d in range(10)]
    # 0.805 now, falling 0.005/day -> 0.75 in 11 days
    assert ind.days_to_threshold(history, 0.75) == pytest.approx(11.0, abs=0.2)
    assert ind.days_to_threshold([(t, 0.85) for t, _ in history], 0.75) is None


# --- Scoring ---


def test_ml_alone_never_raises_an_alerting_level():
    """At 0.38 precision the model alone may only flag MEDIUM (watch);
    HIGH/CRITICAL notify and need physical evidence."""
    top = ml_indicator(1.0, 0.558, None)
    assert top.score == ML_MAX_SCORE
    score, level, _, _ = combine([top])
    assert level in ("LOW", "MEDIUM")

    physical = ind.Indicator("performance_ratio", "PV_ARRAY", "PR", 0.6, "ratio", 0.75, 40.0, "")
    _, combined_level, _, _ = combine([top, physical])
    assert combined_level == "HIGH"  # model + real evidence escalates


def test_noisy_or_compounds_moderate_signals():
    make = lambda s: ind.Indicator("x", "C", "x", 0, "", None, s, "")
    single, _, _, _ = combine([make(40)])
    double, _, _, _ = combine([make(40), make(40)])
    assert single == 40 and double == 64
    assert level_for(0) == "LOW" and level_for(80) == "CRITICAL"


# --- API (real DB) ---


def _admin_headers() -> dict:
    email = f"failure-pred-{uuid.uuid4().hex[:10]}@pytest.solarflow.com"
    client.post("/api/v1/auth/register", json={
        "email": email, "password": "TestPass123!",
        "full_name": "Failure Prediction Admin", "organization_name": "Failure Prediction Org",
    })
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "TestPass123!"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _factory_with_inverter(headers: dict, pr: float) -> tuple[int, int]:
    factory = client.post(
        "/api/v1/factories",
        json={"name": "Failure Prediction Factory", "solar_capacity_kw": 500.0},
        headers=headers,
    ).json()
    device = client.post(
        f"/api/v1/factories/{factory['id']}/devices",
        json={"name": "Inverter A", "device_type": "INVERTER", "connection_type": "API"},
        headers=headers,
    ).json()

    # Four hours of telemetry ending now, stamped on a clock shifted so
    # the synthetic sun is up regardless of when the test runs.
    now = datetime.now(timezone.utc).replace(microsecond=0)
    synthetic_start = datetime(2026, 6, 15, 8, 0, tzinfo=timezone.utc)
    points = _synthetic_day(synthetic_start, 4, pr=pr, step_s=60)
    offset = now - (synthetic_start + timedelta(hours=4))

    db = SessionLocal()
    try:
        db.add_all([
            DeviceEnergyReading(
                factory_id=factory["id"], device_id=device["id"],
                timestamp=p.timestamp + offset, power_kw=p.power_kw, voltage=p.voltage,
                temperature_c=p.temperature_c, raw_data=p.raw_data,
                status="ONLINE", data_quality="GOOD",
            )
            for p in points
        ])
        db_device = db.get(Device, device["id"])
        db_device.status = "ONLINE"
        db_device.last_seen_at = now
        db.commit()
    finally:
        db.close()
    return factory["id"], device["id"]


def test_assess_endpoint_scores_inverter_with_ml():
    headers = _admin_headers()
    factory_id, device_id = _factory_with_inverter(headers, pr=0.82)

    res = client.post(f"/api/v1/factories/{factory_id}/failure-prediction/assess", headers=headers)
    assert res.status_code == 200
    body = res.json()
    row = next(d for d in body["devices"] if d["device_id"] == device_id)
    assessment = row["assessment"]

    assert assessment["ml_status"] == "OK"
    assert assessment["method"] == "ML+RULES"
    assert 0 <= assessment["failure_probability"] <= 1
    codes = {i["code"] for i in assessment["indicators"]}
    assert {"performance_ratio", "ml_fault_probability", "data_gaps"} <= codes

    history = client.get(
        f"/api/v1/factories/{factory_id}/failure-prediction/devices/{device_id}/history",
        headers=headers,
    ).json()
    assert len(history) == 1


def test_degraded_array_raises_critical_alert():
    headers = _admin_headers()
    factory_id, device_id = _factory_with_inverter(headers, pr=0.40)

    body = client.post(f"/api/v1/factories/{factory_id}/failure-prediction/assess", headers=headers).json()
    assessment = next(d for d in body["devices"] if d["device_id"] == device_id)["assessment"]
    assert assessment["risk_level"] == "CRITICAL"
    assert assessment["top_reason"] == "performance_ratio"
    assert body["counts"]["CRITICAL"] == 1

    db = SessionLocal()
    try:
        alert = db.scalar(select(Notification).where(
            Notification.factory_id == factory_id,
            Notification.rule_id == f"FAILURE_RISK:{device_id}",
        ))
        assert alert is not None and alert.severity == "CRITICAL"
    finally:
        db.close()


def test_failure_events_log_and_tenant_scoping():
    headers = _admin_headers()
    factory_id, device_id = _factory_with_inverter(headers, pr=0.82)
    event = {
        "device_id": device_id, "occurred_at": "2026-09-01T10:00:00Z",
        "failure_type": "STRING_FAULT", "severity": "HIGH", "description": "Blown string fuse",
    }
    created = client.post(f"/api/v1/factories/{factory_id}/failure-prediction/events", json=event, headers=headers)
    assert created.status_code == 201
    listed = client.get(f"/api/v1/factories/{factory_id}/failure-prediction/events", headers=headers).json()
    assert [e["failure_type"] for e in listed] == ["STRING_FAULT"]

    other_factory, _ = _factory_with_inverter(headers, pr=0.82)
    wrong = client.post(f"/api/v1/factories/{other_factory}/failure-prediction/events", json=event, headers=headers)
    assert wrong.status_code == 404

    outsider = _admin_headers()
    assert client.get(f"/api/v1/factories/{factory_id}/failure-prediction/overview", headers=outsider).status_code == 404


def test_model_info_reports_honest_metrics():
    headers = _admin_headers()
    factory_id, _ = _factory_with_inverter(headers, pr=0.82)
    info = client.get(f"/api/v1/factories/{factory_id}/failure-prediction/model", headers=headers).json()
    assert info["horizon_minutes"] == 180
    assert 0.5 < info["test_metrics"]["roc_auc"] < 0.9
    assert info["limitations"]
