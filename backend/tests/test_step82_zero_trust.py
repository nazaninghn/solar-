import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.core.api_rate_limit import _record_and_check, _requests
from app.core.config import settings
from app.core.security import hash_password
from app.database.session import SessionLocal
from app.main import app
from app.models.organization import Organization
from app.models.user import User
from app.modules.admin.models import APIKey
from app.modules.security.models import SecurityEvent

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
            "full_name": "Pytest Zero Trust User",
            "organization_name": org_name,
        },
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()
    return {**login, "email": email}


# --- Security event logging (82) ---


def test_login_failure_logs_security_event():
    db = SessionLocal()
    try:
        email = _unique_email("login-fail")
        response = client.post(
            "/api/v1/auth/login", json={"email": email, "password": "WrongPassword123!"}
        )
        assert response.status_code == 401

        event = (
            db.query(SecurityEvent)
            .filter(
                SecurityEvent.event_type == "LOGIN_FAILED",
                SecurityEvent.description.like(f"%{email}%"),
            )
            .first()
        )
        assert event is not None
    finally:
        db.close()


def test_login_success_logs_security_event():
    db = SessionLocal()
    try:
        tokens = _register_and_login("login-success", f"Login Success Co {uuid.uuid4().hex[:6]}")
        user = db.query(User).filter(User.email == tokens["email"]).first()

        event = (
            db.query(SecurityEvent)
            .filter(
                SecurityEvent.event_type == "LOGIN_SUCCESS",
                SecurityEvent.user_id == user.id,
            )
            .first()
        )
        assert event is not None
    finally:
        db.close()


def test_permission_denied_logs_security_event():
    db = SessionLocal()
    org = None
    try:
        # A fresh self-registration is always COMPANY_ADMIN, which holds
        # every permission — need a VIEWER (created directly) to actually
        # hit require_permission()'s deny path, as opposed to
        # ai-readiness's separate _require_super_admin gate.
        now = datetime.now(timezone.utc)
        org = Organization(name=f"Perm Denied Co {uuid.uuid4().hex[:6]}", created_at=now, updated_at=now)
        db.add(org)
        db.flush()

        email = _unique_email("perm-denied")
        password = "TestPass123!"
        viewer = User(
            organization_id=org.id,
            email=email,
            hashed_password=hash_password(password),
            full_name="Pytest Viewer",
            role="VIEWER",
            is_active=True,
            is_verified=True,
        )
        db.add(viewer)
        db.commit()
        db.refresh(viewer)

        login = client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()

        response = client.get(
            "/api/v1/company/users",
            headers={"Authorization": f"Bearer {login['access_token']}"},
        )
        assert response.status_code == 403

        event = (
            db.query(SecurityEvent)
            .filter(
                SecurityEvent.event_type == "PERMISSION_DENIED",
                SecurityEvent.user_id == viewer.id,
            )
            .first()
        )
        assert event is not None
    finally:
        if org is not None:
            db.query(User).filter(User.organization_id == org.id).delete(synchronize_session=False)
            db.query(Organization).filter(Organization.id == org.id).delete()
        db.commit()
        db.close()


def test_refresh_token_reuse_logs_high_severity_event():
    db = SessionLocal()
    try:
        tokens = _register_and_login("token-reuse", f"Token Reuse Co {uuid.uuid4().hex[:6]}")
        user = db.query(User).filter(User.email == tokens["email"]).first()

        # First refresh rotates the token (succeeds).
        first = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        assert first.status_code == 200

        # Reusing the now-revoked original refresh token is theft-shaped.
        second = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        assert second.status_code == 401

        event = (
            db.query(SecurityEvent)
            .filter(
                SecurityEvent.event_type == "TOKEN_REUSE",
                SecurityEvent.user_id == user.id,
            )
            .first()
        )
        assert event is not None
        assert event.severity == "HIGH"
    finally:
        db.close()


def test_invalid_device_key_logs_security_event():
    db = SessionLocal()
    try:
        response = client.post(
            "/api/v1/devices/999999999/telemetry",
            headers={"X-Device-Key": "not-a-real-key"},
            json={"timestamp": datetime.now(timezone.utc).isoformat()},
        )
        assert response.status_code == 401

        event = (
            db.query(SecurityEvent)
            .filter(
                SecurityEvent.event_type == "SUSPICIOUS_REQUEST",
                SecurityEvent.description.like("%device_id=999999999%"),
            )
            .first()
        )
        assert event is not None
    finally:
        db.close()


# --- General API rate limiting (82) ---


def test_rate_limit_sliding_window_blocks_after_threshold():
    key = f"pytest-unit-{uuid.uuid4().hex[:8]}"
    original_limit = settings.API_RATE_LIMIT_PER_MINUTE
    settings.API_RATE_LIMIT_PER_MINUTE = 3
    try:
        assert _record_and_check(key) is False
        assert _record_and_check(key) is False
        assert _record_and_check(key) is False
        # 4th request within the window exceeds the limit of 3.
        assert _record_and_check(key) is True
    finally:
        settings.API_RATE_LIMIT_PER_MINUTE = original_limit
        _requests.pop(key, None)


def test_rate_limit_is_per_key_not_global():
    key_a = f"pytest-unit-a-{uuid.uuid4().hex[:8]}"
    key_b = f"pytest-unit-b-{uuid.uuid4().hex[:8]}"
    original_limit = settings.API_RATE_LIMIT_PER_MINUTE
    settings.API_RATE_LIMIT_PER_MINUTE = 1
    try:
        assert _record_and_check(key_a) is False
        assert _record_and_check(key_a) is True
        # A different key has its own independent budget.
        assert _record_and_check(key_b) is False
    finally:
        settings.API_RATE_LIMIT_PER_MINUTE = original_limit
        _requests.pop(key_a, None)
        _requests.pop(key_b, None)


# --- API key service identity (82) ---


def test_api_key_authenticates_and_scopes_to_own_organization():
    db = SessionLocal()
    org = None
    try:
        now = datetime.now(timezone.utc)
        org = Organization(name=f"Pytest API Key Org {uuid.uuid4().hex[:8]}", created_at=now, updated_at=now)
        db.add(org)
        db.flush()

        import hashlib
        import secrets

        raw_key = f"sf_{secrets.token_urlsafe(32)}"
        api_key = APIKey(
            organization_id=org.id,
            name="Pytest Integration Key",
            key_prefix=raw_key[:7],
            hashed_key=hashlib.sha256(raw_key.encode()).hexdigest(),
            created_at=now,
        )
        db.add(api_key)
        db.commit()

        response = client.get(
            "/api/v1/integrations/energy-summary", headers={"X-API-Key": raw_key}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["organization_id"] == org.id
        assert body["factories"] == []

        db.refresh(api_key)
        assert api_key.last_used_at is not None
    finally:
        if org is not None:
            db.query(APIKey).filter(APIKey.organization_id == org.id).delete(synchronize_session=False)
            db.query(Organization).filter(Organization.id == org.id).delete()
        db.commit()
        db.close()


def test_api_key_rejects_invalid_key():
    response = client.get(
        "/api/v1/integrations/energy-summary", headers={"X-API-Key": "sf_totally-invalid"}
    )
    assert response.status_code == 401


def test_api_key_rejects_revoked_key():
    db = SessionLocal()
    org = None
    try:
        now = datetime.now(timezone.utc)
        org = Organization(name=f"Pytest Revoked Key Org {uuid.uuid4().hex[:8]}", created_at=now, updated_at=now)
        db.add(org)
        db.flush()

        import hashlib
        import secrets

        raw_key = f"sf_{secrets.token_urlsafe(32)}"
        api_key = APIKey(
            organization_id=org.id,
            name="Pytest Revoked Key",
            key_prefix=raw_key[:7],
            hashed_key=hashlib.sha256(raw_key.encode()).hexdigest(),
            revoked_at=now,
            created_at=now,
        )
        db.add(api_key)
        db.commit()

        response = client.get(
            "/api/v1/integrations/energy-summary", headers={"X-API-Key": raw_key}
        )
        assert response.status_code == 401
    finally:
        if org is not None:
            db.query(APIKey).filter(APIKey.organization_id == org.id).delete(synchronize_session=False)
            db.query(Organization).filter(Organization.id == org.id).delete()
        db.commit()
        db.close()


def test_api_key_missing_header_rejected():
    response = client.get("/api/v1/integrations/energy-summary")
    assert response.status_code == 401
