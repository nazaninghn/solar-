import threading
import time
import uuid
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.database.session import SessionLocal
from app.main import app
from app.models.organization import Organization
from app.modules.performance.models import TenantQuota
from app.modules.performance.quota_enforcement import _get_quota_locked

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
            "full_name": "Pytest QA User",
            "organization_name": org_name,
        },
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()
    return {**login, "email": email}


# --- Concurrency: quota enforcement locking (85.32) ---


def test_quota_lock_serializes_concurrent_access():
    """85: deterministic proof _get_quota_locked's SELECT ... FOR
    UPDATE actually blocks a second session, rather than relying on
    HTTP-level timing (which is noisy and didn't reliably reproduce
    the underlying race in manual testing)."""
    db_setup = SessionLocal()
    org = None
    try:
        now = datetime.now(timezone.utc)
        org = Organization(name=f"Pytest Lock Org {uuid.uuid4().hex[:8]}", created_at=now, updated_at=now)
        db_setup.add(org)
        db_setup.commit()
        db_setup.refresh(org)
        org_id = org.id

        holder_acquired = threading.Event()
        holder_release = threading.Event()
        second_acquired_at = {}

        def _hold_lock():
            db = SessionLocal()
            try:
                _get_quota_locked(db, org_id)
                holder_acquired.set()
                holder_release.wait(timeout=5)
            finally:
                db.commit()
                db.close()

        holder_thread = threading.Thread(target=_hold_lock)
        holder_thread.start()
        assert holder_acquired.wait(timeout=5), "first session never acquired the lock"

        def _try_second_acquire():
            db = SessionLocal()
            try:
                start = time.monotonic()
                _get_quota_locked(db, org_id)
                second_acquired_at["elapsed"] = time.monotonic() - start
            finally:
                db.commit()
                db.close()

        second_thread = threading.Thread(target=_try_second_acquire)
        second_thread.start()

        # The second acquire should be BLOCKED while the first holds
        # the row lock - give it a moment, then release the first and
        # confirm the second only completes afterward.
        time.sleep(0.3)
        assert "elapsed" not in second_acquired_at, "second session acquired the lock while the first still held it"

        holder_release.set()
        holder_thread.join(timeout=5)
        second_thread.join(timeout=5)

        assert "elapsed" in second_acquired_at
        # It should have waited at least close to the ~0.3s hold above.
        assert second_acquired_at["elapsed"] >= 0.2
    finally:
        if org is not None:
            db_setup.query(TenantQuota).filter(TenantQuota.organization_id == org.id).delete(synchronize_session=False)
            db_setup.query(Organization).filter(Organization.id == org.id).delete()
        db_setup.commit()
        db_setup.close()


def test_quota_enforcement_still_works_after_locking_change():
    tokens = _register_and_login("quota-still-works", f"Quota Still Works Co {uuid.uuid4().hex[:6]}")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Default max_factories is 5 - create 5, the 6th must be rejected.
    for i in range(5):
        response = client.post(
            "/api/v1/factories", headers=headers, json={"name": f"Factory {i}", "timezone": "UTC"}
        )
        assert response.status_code == 201, response.text

    sixth = client.post(
        "/api/v1/factories", headers=headers, json={"name": "One Too Many", "timezone": "UTC"}
    )
    assert sixth.status_code == 429


# --- Error message leakage (85.39) ---


def test_unhandled_exception_does_not_leak_internal_details():
    tokens = _register_and_login("error-leak", f"Error Leak Co {uuid.uuid4().hex[:6]}")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # can_access_factory (the thing we're about to make explode) is only
    # invoked per-factory inside list_factories's comprehension - a
    # freshly-registered org has none, so create one first.
    client.post("/api/v1/factories", headers=headers, json={"name": "Trigger Factory", "timezone": "UTC"})

    secret_detail = "DATABASE_PASSWORD=hunter2-should-never-appear-in-response"
    # raise_server_exceptions=False: get the actual HTTP response an
    # external caller would see, instead of re-raising the exception
    # into the test process (TestClient's default).
    non_raising_client = TestClient(app, raise_server_exceptions=False)

    with patch(
        "app.modules.factories.router.can_access_factory",
        side_effect=RuntimeError(secret_detail),
    ):
        response = non_raising_client.get(
            "/api/v1/factories",
            headers=headers,
        )

    assert response.status_code == 500
    body_text = response.text
    assert secret_detail not in body_text
    assert "RuntimeError" not in body_text
    assert "Traceback" not in body_text
    assert "app/modules" not in body_text and "app\\modules" not in body_text


# --- Idempotency (85.33) ---


def test_completing_a_drill_twice_is_idempotent():
    """Reuses the disaster-recovery drill flow (Step 83) as a real
    sensitive-operation idempotency check: completing an already-
    completed drill must not error or double-apply side effects."""
    tokens = _register_and_login("idempotent-drill", f"Idempotent Drill Co {uuid.uuid4().hex[:6]}")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    client.post("/api/v1/admin/disaster-recovery/targets/refresh", headers=headers)
    create = client.post(
        "/api/v1/admin/disaster-recovery/drills",
        headers=headers,
        json={"scenario": "Idempotency Test Drill", "target_service": "API", "environment": "staging"},
    )
    drill_id = create.json()["id"]

    first = client.post(f"/api/v1/admin/disaster-recovery/drills/{drill_id}/complete", headers=headers)
    second = client.post(f"/api/v1/admin/disaster-recovery/drills/{drill_id}/complete", headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == "COMPLETED"
    assert second.json()["status"] == "COMPLETED"
