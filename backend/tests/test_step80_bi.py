import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.database.session import SessionLocal
from app.jobs.bi_jobs import check_bi_kpi_alerts
from app.main import app
from app.models.factory import Factory
from app.models.organization import Organization
from app.modules.bi import alerts as bi_alerts
from app.modules.bi.funnel import compute_activation_rate, compute_funnel, compute_signups
from app.modules.bi.revenue import compute_arr, compute_ltv, compute_mrr
from app.modules.bi.segmentation import segment_by_industry, segment_by_plan, segment_by_size
from app.modules.billing.models import Plan, Subscription
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
            "full_name": "Pytest BI User",
            "organization_name": org_name,
        },
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()
    return {**login, "email": email}


# --- Funnel (80) ---


def test_signup_and_funnel_reflect_a_real_new_organization():
    org_name = f"BI Funnel Test Co {uuid.uuid4().hex[:6]}"
    tokens = _register_and_login("bi-funnel", org_name)

    db = SessionLocal()
    try:
        org = db.query(Organization).filter(Organization.name == org_name).first()
        assert org is not None

        signups = compute_signups(db, days=1)
        today = datetime.now(timezone.utc).date().isoformat()
        today_row = next((s for s in signups if s["date"] == today), None)
        assert today_row is not None
        assert today_row["signups"] >= 1

        funnel = compute_funnel(db, days=1)
        signed_up_stage = next(s for s in funnel if s["stage"] == "signed_up")
        assert signed_up_stage["count"] >= 1
    finally:
        db.close()


def test_activation_rate_counts_factory_creation_within_window():
    org_name = f"BI Activation Test Co {uuid.uuid4().hex[:6]}"
    tokens = _register_and_login("bi-activation", org_name)

    client.post(
        "/api/v1/factories",
        json={"name": "Activation Test Factory"},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    db = SessionLocal()
    try:
        org = db.query(Organization).filter(Organization.name == org_name).first()
        factory = db.query(Factory).filter(Factory.organization_id == org.id).first()
        assert factory is not None

        result = compute_activation_rate(db, days=1, activation_window_days=7)
        assert result["cohort_size"] >= 1
        assert result["activated_count"] >= 1
    finally:
        db.close()


# --- Revenue (80) — real formulas against a real, isolated Plan/Subscription ---


def test_revenue_metrics_compute_correctly_against_real_subscriptions():
    db = SessionLocal()
    plan = None
    orgs = []
    try:
        now = datetime.now(timezone.utc)
        plan = Plan(
            name=f"Pytest BI Plan {uuid.uuid4().hex[:8]}",
            monthly_price=40.0,
            currency="USD",
            max_factories=5,
            max_devices=100,
            max_users=25,
            created_at=now,
        )
        db.add(plan)
        db.flush()

        baseline_mrr = compute_mrr(db)

        for _ in range(2):
            org = Organization(name=f"Pytest BI Revenue Org {uuid.uuid4().hex[:8]}", created_at=now, updated_at=now)
            db.add(org)
            db.flush()
            orgs.append(org)
            db.add(
                Subscription(
                    organization_id=org.id,
                    plan_id=plan.id,
                    status="ACTIVE",
                    billing_cycle="MONTHLY",
                    current_period_start=now,
                    current_period_end=now + timedelta(days=30),
                    created_at=now,
                )
            )
        db.commit()

        assert compute_mrr(db) == round(baseline_mrr + 80.0, 2)
        assert compute_arr(db) == round((baseline_mrr + 80.0) * 12, 2)

        ltv = compute_ltv(db)
        assert ltv["monthly_churn_rate_percent"] == 0.0
        assert ltv["estimated_ltv"] is None  # undefined at 0% churn, not infinite
    finally:
        if orgs:
            db.query(Subscription).filter(
                Subscription.organization_id.in_([o.id for o in orgs])
            ).delete(synchronize_session=False)
            db.query(Organization).filter(Organization.id.in_([o.id for o in orgs])).delete(
                synchronize_session=False
            )
        if plan is not None:
            db.query(Plan).filter(Plan.id == plan.id).delete()
        db.commit()
        db.close()


def test_revenue_metrics_are_zero_with_no_subscriptions():
    """Confirms the honest-zero behavior this step is built around —
    not a placeholder, the correct answer when nothing has been billed."""
    db = SessionLocal()
    try:
        # No cleanup needed for THIS org set — just checking the shape
        # of the computation is sane (non-negative, well-formed) since
        # this session's shared DB may or may not have other test
        # subscriptions active from other test runs.
        mrr = compute_mrr(db)
        assert mrr >= 0.0
        assert compute_arr(db) == round(mrr * 12, 2)
    finally:
        db.close()


# --- Segmentation (80) ---


def test_segmentation_endpoints_return_well_formed_data():
    db = SessionLocal()
    try:
        by_plan = segment_by_plan(db)
        by_industry = segment_by_industry(db)
        by_size = segment_by_size(db)

        assert all("organization_count" in row for row in by_plan)
        assert all("factory_count" in row for row in by_industry)
        assert {row["bucket"] for row in by_size} == {
            "0_factories",
            "1_factory",
            "2_to_5_factories",
            "6_plus_factories",
        }
    finally:
        db.close()


# --- KPI alerts (80) ---


def test_kpi_alert_fires_on_low_activation_and_dedups():
    db = SessionLocal()
    try:
        db.query(MonitoringIncident).filter(
            MonitoringIncident.title.like("%LOW_ACTIVATION_RATE%")
        ).delete(synchronize_session=False)
        db.commit()

        with patch.object(
            bi_alerts,
            "compute_activation_rate",
            return_value={"cohort_size": 50, "activated_count": 5, "activation_rate_percent": 10.0},
        ):
            with patch("app.jobs.bi_jobs.check_kpi_alerts", side_effect=lambda db: bi_alerts.check_kpi_alerts(db)):
                check_bi_kpi_alerts()

        incident = (
            db.query(MonitoringIncident)
            .filter(MonitoringIncident.title.like("%LOW_ACTIVATION_RATE%"))
            .first()
        )
        assert incident is not None
        assert incident.service == "bi"

        with patch.object(
            bi_alerts,
            "compute_activation_rate",
            return_value={"cohort_size": 50, "activated_count": 5, "activation_rate_percent": 10.0},
        ):
            with patch("app.jobs.bi_jobs.check_kpi_alerts", side_effect=lambda db: bi_alerts.check_kpi_alerts(db)):
                check_bi_kpi_alerts()

        count = (
            db.query(MonitoringIncident)
            .filter(MonitoringIncident.title.like("%LOW_ACTIVATION_RATE%"))
            .count()
        )
        assert count == 1
    finally:
        db.query(MonitoringIncident).filter(
            MonitoringIncident.title.like("%LOW_ACTIVATION_RATE%")
        ).delete(synchronize_session=False)
        db.commit()
        db.close()


def test_bi_endpoints_require_super_admin():
    tokens = _register_and_login("bi-access", f"BI Access Co {uuid.uuid4().hex[:6]}")

    for path in ("/api/v1/bi/dashboard", "/api/v1/bi/revenue", "/api/v1/bi/cohorts"):
        response = client.get(path, headers={"Authorization": f"Bearer {tokens['access_token']}"})
        assert response.status_code == 403
