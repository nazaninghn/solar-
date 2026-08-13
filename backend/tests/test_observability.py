import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.core.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, CircuitState
from app.core.freshness import compute_freshness
from app.core.metrics import _request_metrics, get_request_metrics_snapshot, record_request
from app.main import app
from app.models.factory import Factory
from app.models.notification import Notification
from app.modules.notifications.engine import _create_from_rule
from app.notifications.rules import BatteryLowRule, BatteryRuleContext

client = TestClient(app)


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}@pytest.solarflow.com"


def _register_and_login() -> str:
    email = _unique_email("observability-admin")

    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPass123!",
            "full_name": "Observability Admin",
            "organization_name": "Observability Test Org",
        },
    )

    login = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "TestPass123!"}
    )

    return login.json()["access_token"]


# --- Circuit breaker (28.23) ---


def test_circuit_breaker_opens_after_threshold_and_recovers():
    async def run():
        cb = CircuitBreaker("test_service", failure_threshold=3, recovery_timeout_seconds=0.1)

        async def failing():
            raise ValueError("boom")

        async def succeeding():
            return "ok"

        for _ in range(3):
            try:
                await cb.call(failing)
            except ValueError:
                pass

        assert cb.state == CircuitState.OPEN

        try:
            await cb.call(succeeding)
            raised = False
        except CircuitBreakerOpenError:
            raised = True
        assert raised is True

        await asyncio.sleep(0.15)
        assert cb.state == CircuitState.HALF_OPEN

        result = await cb.call(succeeding)
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED

    asyncio.run(run())


# --- Metrics (28.10) ---


def test_request_metrics_snapshot_reflects_recorded_requests():
    _request_metrics.total = 0
    _request_metrics.errors_5xx = 0
    _request_metrics.total_duration_ms = 0.0
    _request_metrics.bucket_counts.clear()

    record_request(200, 50.0, "excellent")
    record_request(500, 1200.0, "slow")

    snapshot = get_request_metrics_snapshot()

    assert snapshot["total_requests"] == 2
    assert snapshot["total_errors_5xx"] == 1
    assert snapshot["error_rate_percent"] == 50.0


# --- Data freshness (28.25) ---


def test_freshness_recent_timestamp_not_stale():
    result = compute_freshness(datetime.now(timezone.utc))
    assert result["is_stale"] is False


def test_freshness_old_timestamp_is_stale():
    old = datetime.now(timezone.utc) - timedelta(hours=5)
    result = compute_freshness(old, stale_after_minutes=120)
    assert result["is_stale"] is True
    assert result["age_minutes"] > 200


# --- Request-ID middleware (28.6-28.8) ---


def test_response_includes_request_id_header():
    response = client.get("/health")
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"].startswith("req_")


# --- Alert auto-recovery (28.29) ---


def test_alert_auto_resolves_when_condition_clears(db_session=None):
    from app.database.session import SessionLocal

    db = SessionLocal()
    try:
        factory = db.query(Factory).first()
        rule = BatteryLowRule()

        violation = rule.evaluate(BatteryRuleContext(soc_percent=5))
        _create_from_rule(db, factory, "BATTERY", rule, violation)

        active = (
            db.query(Notification)
            .filter(
                Notification.factory_id == factory.id,
                Notification.rule_id == "BATTERY_LOW",
            )
            .order_by(Notification.id.desc())
            .first()
        )
        assert active.status == "UNREAD"

        recovered = rule.evaluate(BatteryRuleContext(soc_percent=80))
        _create_from_rule(db, factory, "BATTERY", rule, recovered)

        db.refresh(active)
        assert active.status == "RESOLVED"
        assert active.resolved_at is not None
    finally:
        db.close()


# --- System endpoints permission gating ---


def test_system_health_requires_super_admin():
    token = _register_and_login()

    response = client.get(
        "/api/v1/system/health", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_system_metrics_requires_super_admin():
    token = _register_and_login()

    response = client.get(
        "/api/v1/system/metrics", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_health_ready_checks_database():
    response = client.get("/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["database"] == "ok"
