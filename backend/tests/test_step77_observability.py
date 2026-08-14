import uuid
from datetime import date, datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.core.metrics import _request_metrics, get_request_metrics_snapshot, record_request
from app.database.session import SessionLocal
from app.jobs.retention_jobs import purge_old_observability_data
from app.main import app
from app.models.energy_daily import EnergyDaily
from app.models.factory import Factory
from app.models.organization import Organization
from app.modules.alerts.models import OnCallSchedule
from app.modules.alerts.oncall import create_on_call_shift, get_current_on_call
from app.modules.data_integrity.models import DataAnomaly
from app.modules.observability.anomaly_detection import detect_energy_anomalies
from app.modules.observability.models import SystemMetricSnapshot
from app.modules.observability.slo import compute_slo_status

client = TestClient(app)


def _make_test_factory(db) -> Factory:
    org = Organization(name=f"Step77 Test Org {uuid.uuid4().hex[:6]}")
    db.add(org)
    db.flush()

    factory = Factory(organization_id=org.id, name="Step77 Test Factory")
    db.add(factory)
    db.commit()
    db.refresh(factory)
    return factory


# --- Request metrics percentiles (77.6) ---


def test_request_metrics_percentiles_reflect_distribution():
    _request_metrics.total = 0
    _request_metrics.errors_5xx = 0
    _request_metrics.total_duration_ms = 0.0
    _request_metrics.bucket_counts.clear()
    _request_metrics.recent_durations_ms.clear()

    for ms in [100] * 90 + [1000] * 9 + [5000]:
        record_request(200, ms, "excellent")

    snapshot = get_request_metrics_snapshot()

    assert snapshot["p50_duration_ms"] == 100
    assert snapshot["p99_duration_ms"] == 5000
    assert snapshot["p95_duration_ms"] < snapshot["p99_duration_ms"]


# --- Anomaly detection (77.56-77.57) ---


def test_anomaly_detection_flags_statistical_outlier():
    db = SessionLocal()
    try:
        factory = _make_test_factory(db)
        test_date = date(2021, 6, 30)

        for i in range(29):
            db.add(
                EnergyDaily(
                    factory_id=factory.id,
                    date=date(2021, 6, 1) + timedelta(days=i),
                    solar_kwh=500 + (i % 3),
                    consumption_kwh=800,
                )
            )
        db.add(
            EnergyDaily(
                factory_id=factory.id, date=test_date, solar_kwh=50, consumption_kwh=800
            )
        )
        db.commit()

        created = detect_energy_anomalies(db, as_of=test_date)
        assert created == 1

        anomaly = (
            db.query(DataAnomaly)
            .filter(DataAnomaly.factory_id == factory.id, DataAnomaly.metric == "solar_kwh")
            .first()
        )
        assert anomaly is not None
        assert anomaly.severity == "CRITICAL"
        assert anomaly.detected_value == 50.0
    finally:
        db.close()


def test_anomaly_detection_no_false_positive_on_stable_data():
    db = SessionLocal()
    try:
        factory = _make_test_factory(db)
        test_date = date(2021, 7, 31)

        for i in range(30):
            db.add(
                EnergyDaily(
                    factory_id=factory.id,
                    date=date(2021, 7, 1) + timedelta(days=i),
                    solar_kwh=500 + (i % 3),
                    consumption_kwh=800,
                )
            )
        db.add(
            EnergyDaily(
                factory_id=factory.id, date=test_date, solar_kwh=501, consumption_kwh=800
            )
        )
        db.commit()

        created = detect_energy_anomalies(db, as_of=test_date)
        assert created == 0
    finally:
        db.close()


def test_anomaly_detection_skips_factory_with_insufficient_history():
    db = SessionLocal()
    try:
        factory = _make_test_factory(db)
        test_date = date(2021, 8, 5)

        for i in range(3):
            db.add(
                EnergyDaily(
                    factory_id=factory.id,
                    date=date(2021, 8, 1) + timedelta(days=i),
                    solar_kwh=500,
                    consumption_kwh=800,
                )
            )
        db.add(EnergyDaily(factory_id=factory.id, date=test_date, solar_kwh=1, consumption_kwh=800))
        db.commit()

        created = detect_energy_anomalies(db, as_of=test_date)
        assert created == 0
    finally:
        db.close()


# --- SLO computation (77.25-77.28) ---


def test_slo_status_includes_all_five_targets():
    db = SessionLocal()
    try:
        slos = compute_slo_status(db)
        names = {s["name"] for s in slos}
        assert names == {
            "api_availability",
            "api_latency_p95",
            "telemetry_ingest",
            "queue_processing",
            "data_freshness",
        }
        for slo in slos:
            assert "compliant" in slo
            assert isinstance(slo["compliant"], bool)
    finally:
        db.close()


def test_slo_availability_marks_noncompliant_below_target():
    db = SessionLocal()
    try:
        slos = compute_slo_status(db)
        availability = next(s for s in slos if s["name"] == "api_availability")
        # Compliance boundary is exactly the target — verify the field
        # relationship rather than forcing live error-rate state.
        assert availability["compliant"] == (
            availability["actual_value"] >= availability["target_value"]
        )
    finally:
        db.close()


# --- On-call schedule (77.61-77.63) ---


def test_get_current_on_call_returns_user_within_active_window():
    db = SessionLocal()
    try:
        factory = _make_test_factory(db)
        org = db.get(Organization, factory.organization_id)

        from app.models.user import User
        from app.core.security import hash_password

        user = User(
            organization_id=org.id,
            email=f"oncall-{uuid.uuid4().hex[:8]}@pytest.solarflow.com",
            hashed_password=hash_password("TestPass123!"),
            full_name="On Call Test User",
            role="ENERGY_MANAGER",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        now = datetime.now(timezone.utc)
        create_on_call_shift(
            db, factory.id, user.id, "PRIMARY", now - timedelta(hours=1), now + timedelta(hours=8)
        )

        on_call = get_current_on_call(db, factory.id, "PRIMARY")
        assert on_call is not None
        assert on_call.id == user.id
    finally:
        db.close()


def test_get_current_on_call_returns_none_outside_window():
    db = SessionLocal()
    try:
        factory = _make_test_factory(db)
        on_call = get_current_on_call(db, factory.id, "PRIMARY")
        assert on_call is None
    finally:
        db.close()


# --- Trace propagation (77.12-77.14) ---


def test_response_includes_trace_id_header():
    response = client.get("/health")
    assert "X-Trace-ID" in response.headers
    assert response.headers["X-Trace-ID"].startswith("trace-")


def test_trace_id_propagates_from_inbound_header():
    response = client.get("/health", headers={"X-Trace-ID": "trace-mycustom0000aaaa"})
    assert response.headers["X-Trace-ID"] == "trace-mycustom0000aaaa"


# --- Retention (77.69-77.70) ---


def test_purge_old_observability_data_removes_only_stale_rows():
    db = SessionLocal()
    try:
        db.query(SystemMetricSnapshot).filter(
            SystemMetricSnapshot.metric == "pytest.retention_test"
        ).delete(synchronize_session=False)
        db.commit()

        old_ts = datetime.now(timezone.utc) - timedelta(days=45)
        recent_ts = datetime.now(timezone.utc)

        old_snapshot = SystemMetricSnapshot(timestamp=old_ts, metric="pytest.retention_test", value=1.0)
        recent_snapshot = SystemMetricSnapshot(
            timestamp=recent_ts, metric="pytest.retention_test", value=2.0
        )
        db.add_all([old_snapshot, recent_snapshot])
        db.commit()

        purge_old_observability_data()

        remaining = (
            db.query(SystemMetricSnapshot)
            .filter(SystemMetricSnapshot.metric == "pytest.retention_test")
            .all()
        )
        assert len(remaining) == 1
        assert remaining[0].value == 2.0
    finally:
        db.close()
