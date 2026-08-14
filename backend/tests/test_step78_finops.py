import uuid
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.core.metrics import flush_and_reset_org_metrics, record_org_request
from app.database.session import SessionLocal
from app.jobs.finops_jobs import check_budget_alerts, flush_api_usage_metrics
from app.main import app
from app.models.organization import Organization
from app.models.user import User
from app.modules.admin.models import APIUsageMetric
from app.modules.finops.models import BudgetThreshold, InfrastructureCost
from app.modules.finops.service import (
    check_budget_thresholds,
    compute_cost_per_organization,
    create_budget_threshold,
    create_infrastructure_cost,
    get_total_monthly_cost_usd,
)
from app.modules.monitoring.models import MonitoringIncident
from app.modules.performance.quota_enforcement import get_quota

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
            "full_name": "Pytest FinOps User",
            "organization_name": org_name,
        },
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()
    return {**login, "email": email, "password": password}


def _get_user(db, email: str) -> User:
    return db.query(User).filter(User.email == email).first()


# --- Quota enforcement (78: wired, previously dead code) ---


def test_factory_quota_blocks_over_limit_creation():
    tokens = _register_and_login("finops-quota-factory", f"Quota Factory Co {uuid.uuid4().hex[:6]}")

    db = SessionLocal()
    try:
        user = _get_user(db, tokens["email"])
        quota = get_quota(db, user.organization_id)
        quota.max_factories = 1
        db.commit()
    finally:
        db.close()

    first = client.post(
        "/api/v1/factories",
        json={"name": "Factory One"},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/factories",
        json={"name": "Factory Two"},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert second.status_code == 429


def test_user_quota_blocks_over_limit_creation():
    tokens = _register_and_login("finops-quota-user", f"Quota User Co {uuid.uuid4().hex[:6]}")

    db = SessionLocal()
    try:
        user = _get_user(db, tokens["email"])
        quota = get_quota(db, user.organization_id)
        # 1 already exists (the registering admin) -> quota of 1 blocks
        # any further addition immediately.
        quota.max_users = 1
        db.commit()
    finally:
        db.close()

    response = client.post(
        "/api/v1/company/users",
        json={
            "email": _unique_email("finops-quota-user-target"),
            "password": "TargetPass123!",
            "full_name": "Should Be Blocked",
            "role": "VIEWER",
        },
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 429


# --- API usage metering flush (78) ---


def test_flush_api_usage_metrics_writes_rows_for_valid_org():
    db = SessionLocal()
    try:
        org = db.query(Organization).first()
        endpoint = f"/pytest/usage-flush-test-{uuid.uuid4().hex[:8]}"

        flush_and_reset_org_metrics()  # clear any stray state first
        record_org_request(org.id, endpoint, "GET", 200, 40.0)
        record_org_request(org.id, endpoint, "GET", 200, 60.0)
        record_org_request(org.id, endpoint, "GET", 500, 100.0)

        flush_api_usage_metrics()

        row = (
            db.query(APIUsageMetric)
            .filter(APIUsageMetric.organization_id == org.id, APIUsageMetric.endpoint == endpoint)
            .first()
        )
        assert row is not None
        assert row.request_count == 3
        assert row.error_count == 1
        assert row.avg_latency_ms == 67
    finally:
        db.query(APIUsageMetric).filter(APIUsageMetric.endpoint.like("/pytest/usage-flush-test-%")).delete(
            synchronize_session=False
        )
        db.commit()
        db.close()


def test_flush_api_usage_metrics_skips_invalid_org_without_losing_valid_ones():
    db = SessionLocal()
    try:
        org = db.query(Organization).first()
        endpoint = f"/pytest/usage-flush-resilience-{uuid.uuid4().hex[:8]}"

        flush_and_reset_org_metrics()
        record_org_request(org.id, endpoint, "GET", 200, 30.0)
        record_org_request(999999999, endpoint, "GET", 200, 30.0)  # nonexistent org

        flush_api_usage_metrics()

        valid_row = (
            db.query(APIUsageMetric)
            .filter(APIUsageMetric.organization_id == org.id, APIUsageMetric.endpoint == endpoint)
            .first()
        )
        assert valid_row is not None

        invalid_row = (
            db.query(APIUsageMetric)
            .filter(APIUsageMetric.organization_id == 999999999)
            .first()
        )
        assert invalid_row is None
    finally:
        db.query(APIUsageMetric).filter(
            APIUsageMetric.endpoint.like("/pytest/usage-flush-resilience-%")
        ).delete(synchronize_session=False)
        db.commit()
        db.close()


# --- Cost attribution (78) ---


def test_cost_attribution_splits_proportionally_to_usage():
    db = SessionLocal()
    cost = None
    try:
        orgs = db.query(Organization).limit(2).all()
        endpoint = f"/pytest/attribution-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)

        db.query(InfrastructureCost).filter(InfrastructureCost.name.like("Pytest Attribution%")).delete()
        db.commit()

        user = db.query(User).first()
        cost = create_infrastructure_cost(db, "Pytest Attribution Cost", "COMPUTE", 100.0, user)

        db.add(
            APIUsageMetric(
                organization_id=orgs[0].id, endpoint=endpoint, method="GET",
                request_count=75, error_count=0, period_start=now, period_end=now,
            )
        )
        db.add(
            APIUsageMetric(
                organization_id=orgs[1].id, endpoint=endpoint, method="GET",
                request_count=25, error_count=0, period_start=now, period_end=now,
            )
        )
        db.commit()

        attribution = compute_cost_per_organization(db, days=30)
        by_org = {a["organization_id"]: a for a in attribution}

        assert by_org[orgs[0].id]["usage_share_percent"] == 75.0
        assert by_org[orgs[1].id]["usage_share_percent"] == 25.0
    finally:
        db.query(APIUsageMetric).filter(APIUsageMetric.endpoint.like("/pytest/attribution-%")).delete(
            synchronize_session=False
        )
        if cost is not None:
            db.query(InfrastructureCost).filter(InfrastructureCost.id == cost.id).delete()
        db.commit()
        db.close()


# --- Budget alerts (78) ---


def test_budget_alert_opens_incident_when_breached_and_dedups():
    db = SessionLocal()
    cost = None
    threshold = None
    try:
        user = db.query(User).first()

        db.query(InfrastructureCost).filter(InfrastructureCost.name.like("Pytest Budget%")).delete()
        db.query(BudgetThreshold).filter(BudgetThreshold.name.like("Pytest Budget%")).delete()
        db.commit()

        cost = create_infrastructure_cost(db, "Pytest Budget Cost", "COMPUTE", 90.0, user)
        threshold = create_budget_threshold(db, "Pytest Budget Threshold", 100.0, warning_percent=80.0)

        breaches = check_budget_thresholds(db)
        assert any(b["threshold_id"] == threshold.id for b in breaches)

        check_budget_alerts()

        dedup_key = f"BUDGET_THRESHOLD:{threshold.id}"
        incident = (
            db.query(MonitoringIncident)
            .filter(MonitoringIncident.title.like(f"%{dedup_key}%"))
            .first()
        )
        assert incident is not None
        assert incident.service == "finops"

        check_budget_alerts()
        count = (
            db.query(MonitoringIncident)
            .filter(MonitoringIncident.title.like(f"%{dedup_key}%"))
            .count()
        )
        assert count == 1
    finally:
        if threshold is not None:
            db.query(MonitoringIncident).filter(
                MonitoringIncident.title.like(f"%BUDGET_THRESHOLD:{threshold.id}%")
            ).delete(synchronize_session=False)
            db.query(BudgetThreshold).filter(BudgetThreshold.id == threshold.id).delete()
        if cost is not None:
            db.query(InfrastructureCost).filter(InfrastructureCost.id == cost.id).delete()
        db.commit()
        db.close()


def test_finops_endpoints_require_super_admin():
    tokens = _register_and_login("finops-access", f"FinOps Access Co {uuid.uuid4().hex[:6]}")

    for path in ("/api/v1/finops/costs", "/api/v1/finops/cost-attribution", "/api/v1/finops/storage"):
        response = client.get(path, headers={"Authorization": f"Bearer {tokens['access_token']}"})
        assert response.status_code == 403
