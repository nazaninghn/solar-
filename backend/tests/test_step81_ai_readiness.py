import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.database.session import SessionLocal
from app.jobs.ai_readiness_jobs import refresh_model_registry_and_check_drift
from app.main import app
from app.models.energy_daily import EnergyDaily
from app.models.factory import Factory
from app.models.organization import Organization
from app.modules.ai_readiness import drift_detection
from app.modules.ai_readiness.data_readiness import (
    MIN_DAYS_FOR_BASELINE_COMPARISON,
    compute_data_readiness,
)
from app.modules.ai_readiness.drift_detection import detect_forecast_drift
from app.modules.ai_readiness.model_governance import list_model_registry, seed_model_registry
from app.modules.forecasting.models import Forecast, ForecastAccuracy
from app.modules.monitoring.models import MonitoringIncident

client = TestClient(app)


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}@pytest.solarflow.com"


def _register_and_login(prefix: str, org_name: str) -> dict:
    email = _unique_email(prefix)
    password = "TestPass123!"

    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Pytest AI Readiness User",
            "organization_name": org_name,
        },
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()
    return {**login, "email": email}


# --- Data readiness (81) ---


def test_data_readiness_reflects_real_energy_daily_history():
    db = SessionLocal()
    org = None
    try:
        now = datetime.now(timezone.utc)
        org = Organization(name=f"Pytest AI Readiness Data Org {uuid.uuid4().hex[:8]}", created_at=now, updated_at=now)
        db.add(org)
        db.flush()
        factory = Factory(organization_id=org.id, name="Pytest Data Readiness Factory")
        db.add(factory)
        db.flush()

        # 100 days of history -> should cross the baseline-comparison threshold
        start = now.date() - timedelta(days=99)
        for i in range(100):
            db.add(
                EnergyDaily(
                    factory_id=factory.id,
                    date=start + timedelta(days=i),
                    solar_kwh=500,
                    consumption_kwh=800,
                    data_quality="COMPLETE",
                )
            )
        db.commit()

        readiness = compute_data_readiness(db)
        entry = next(r for r in readiness if r["factory_id"] == factory.id)

        assert entry["sample_count"] == 100
        assert entry["span_days"] >= MIN_DAYS_FOR_BASELINE_COMPARISON
        assert entry["ready_for_baseline_comparison"] is True
        assert entry["complete_data_ratio"] == 1.0
    finally:
        if org is not None:
            db.query(EnergyDaily).filter(
                EnergyDaily.factory_id.in_(
                    db.query(Factory.id).filter(Factory.organization_id == org.id)
                )
            ).delete(synchronize_session=False)
            db.query(Factory).filter(Factory.organization_id == org.id).delete(synchronize_session=False)
            db.query(Organization).filter(Organization.id == org.id).delete()
        db.commit()
        db.close()


# --- Model registry governance (81) ---


def test_model_registry_seeds_two_baseline_models():
    db = SessionLocal()
    try:
        seeded = seed_model_registry(db)
        versions = {m.version for m in seeded}
        assert versions == {"solar-baseline-v1", "load-baseline-v1"}
        assert all(m.status == "PRODUCTION" for m in seeded)

        registry = list_model_registry(db)
        assert len(registry) >= 2
    finally:
        db.close()


def test_model_registry_computes_real_mae_from_accuracy_history():
    db = SessionLocal()
    org = None
    try:
        now = datetime.now(timezone.utc)
        org = Organization(name=f"Pytest AI Readiness MAE Org {uuid.uuid4().hex[:8]}", created_at=now, updated_at=now)
        db.add(org)
        db.flush()
        factory = Factory(organization_id=org.id, name="Pytest MAE Factory")
        db.add(factory)
        db.flush()

        forecast = Forecast(
            factory_id=factory.id, type="SOLAR_GENERATION", model_version="solar-baseline-v1",
            generated_at=now, forecast_start=now, forecast_end=now + timedelta(hours=24), status="READY",
        )
        db.add(forecast)
        db.flush()

        db.add(ForecastAccuracy(forecast_id=forecast.id, factory_id=factory.id, timestamp=now, predicted_value=100, actual_value=90, error=10, absolute_error=10, created_at=now))
        db.add(ForecastAccuracy(forecast_id=forecast.id, factory_id=factory.id, timestamp=now + timedelta(hours=1), predicted_value=50, actual_value=60, error=-10, absolute_error=10, created_at=now))
        db.commit()

        seeded = seed_model_registry(db)
        solar_entry = next(m for m in seeded if m.version == "solar-baseline-v1")
        # >= since real pre-existing accuracy history may also contribute
        assert solar_entry.mae is not None
        assert solar_entry.mae >= 10.0 - 0.01
    finally:
        if org is not None:
            db.query(ForecastAccuracy).filter(
                ForecastAccuracy.factory_id.in_(
                    db.query(Factory.id).filter(Factory.organization_id == org.id)
                )
            ).delete(synchronize_session=False)
            db.query(Forecast).filter(
                Forecast.factory_id.in_(db.query(Factory.id).filter(Factory.organization_id == org.id))
            ).delete(synchronize_session=False)
            db.query(Factory).filter(Factory.organization_id == org.id).delete(synchronize_session=False)
            db.query(Organization).filter(Organization.id == org.id).delete()
        db.commit()
        seed_model_registry(db)  # reset registry to reflect real state again
        db.close()


# --- Drift detection (81) ---


def test_drift_detection_flags_significant_mae_increase():
    db = SessionLocal()
    try:
        def fake_window_mae(db, forecast_type, window_start, window_end, _calls=[0]):
            _calls[0] += 1
            return (20.0, 15) if _calls[0] % 2 == 1 else (10.0, 15)

        with patch.object(drift_detection, "_window_mae", side_effect=fake_window_mae):
            results = detect_forecast_drift(db, forecast_types=("SOLAR_GENERATION",))

        assert results[0]["drifted"] is True
        assert results[0]["drift_percent"] == 100.0
    finally:
        db.close()


def test_drift_detection_does_not_flag_with_insufficient_samples():
    db = SessionLocal()
    try:
        def fake_window_mae(db, forecast_type, window_start, window_end, _calls=[0]):
            _calls[0] += 1
            return (20.0, 2) if _calls[0] % 2 == 1 else (10.0, 2)  # below MIN_SAMPLES_PER_WINDOW

        with patch.object(drift_detection, "_window_mae", side_effect=fake_window_mae):
            results = detect_forecast_drift(db, forecast_types=("SOLAR_GENERATION",))

        assert results[0]["drifted"] is False
        assert results[0]["drift_percent"] is None
    finally:
        db.close()


def test_drift_alert_job_opens_incident_and_dedups():
    db = SessionLocal()
    try:
        db.query(MonitoringIncident).filter(
            MonitoringIncident.title.like("%FORECAST_DRIFT:SOLAR_GENERATION%")
        ).delete(synchronize_session=False)
        db.commit()

        def fake_detect_drift(db, forecast_types=("SOLAR_GENERATION", "LOAD")):
            return [
                {
                    "forecast_type": "SOLAR_GENERATION",
                    "recent_mae": 20.0,
                    "recent_sample_count": 15,
                    "prior_mae": 10.0,
                    "prior_sample_count": 15,
                    "drift_percent": 100.0,
                    "drifted": True,
                }
            ]

        with patch("app.jobs.ai_readiness_jobs.detect_forecast_drift", side_effect=fake_detect_drift):
            refresh_model_registry_and_check_drift()

        incident = (
            db.query(MonitoringIncident)
            .filter(MonitoringIncident.title.like("%FORECAST_DRIFT:SOLAR_GENERATION%"))
            .first()
        )
        assert incident is not None
        assert incident.service == "ai_readiness"

        with patch("app.jobs.ai_readiness_jobs.detect_forecast_drift", side_effect=fake_detect_drift):
            refresh_model_registry_and_check_drift()

        count = (
            db.query(MonitoringIncident)
            .filter(MonitoringIncident.title.like("%FORECAST_DRIFT:SOLAR_GENERATION%"))
            .count()
        )
        assert count == 1
    finally:
        db.query(MonitoringIncident).filter(
            MonitoringIncident.title.like("%FORECAST_DRIFT:SOLAR_GENERATION%")
        ).delete(synchronize_session=False)
        db.commit()
        db.close()


def test_ai_readiness_endpoints_require_super_admin():
    tokens = _register_and_login("ai-readiness-access", f"AI Readiness Access Co {uuid.uuid4().hex[:6]}")

    for path in (
        "/api/v1/ai-readiness/dashboard",
        "/api/v1/ai-readiness/data-readiness",
        "/api/v1/ai-readiness/model-registry",
        "/api/v1/ai-readiness/drift",
    ):
        response = client.get(path, headers={"Authorization": f"Bearer {tokens['access_token']}"})
        assert response.status_code == 403
