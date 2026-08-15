import uuid

from fastapi.testclient import TestClient

from app.database.session import SessionLocal
from app.main import app
from app.models.user import User
from app.modules.security.lockout import LOCKOUT_DURATION_MINUTES, MAX_FAILED_ATTEMPTS
from app.modules.security.models import AccountLockout, SecurityEvent

client = TestClient(app)


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}@pytest.solarflow.com"


def _register(prefix: str, org_name: str) -> dict:
    email = _unique_email(prefix)
    password = "TestPass123!"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Pytest Lockout User",
            "organization_name": org_name,
        },
    )
    return {"email": email, "password": password}


def test_account_locks_after_max_failed_attempts():
    creds = _register("lockout", f"Lockout Co {uuid.uuid4().hex[:6]}")

    for _ in range(MAX_FAILED_ATTEMPTS):
        response = client.post(
            "/api/v1/auth/login", json={"email": creds["email"], "password": "WrongPassword!"}
        )
        assert response.status_code == 401

    # The account is locked at this point - confirmed below directly
    # against the DB. A 6th request (even with the correct password)
    # also gets denied, but by whichever control's threshold it hits
    # first: the login rate limiter (Step 24/82, also 5/min per
    # IP+email) and the lockout threshold are numerically the same
    # here, so this request 401s from the rate limiter rather than
    # exercising the lockout path a second time - both are correct
    # "access denied" outcomes, so this asserts on the DB state
    # instead of asserting a specific status code for that ambiguous
    # boundary request.
    client.post("/api/v1/auth/login", json={"email": creds["email"], "password": creds["password"]})

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == creds["email"]).first()
        lockout = db.query(AccountLockout).filter(AccountLockout.user_id == user.id).first()
        assert lockout is not None
        assert lockout.locked_until is not None
        assert lockout.failed_attempts >= MAX_FAILED_ATTEMPTS

        locked_event = (
            db.query(SecurityEvent)
            .filter(SecurityEvent.event_type == "ACCOUNT_LOCKED", SecurityEvent.user_id == user.id)
            .first()
        )
        assert locked_event is not None
        assert locked_event.severity == "HIGH"
    finally:
        db.close()


def test_successful_login_resets_failed_attempt_counter():
    creds = _register("lockout-reset", f"Lockout Reset Co {uuid.uuid4().hex[:6]}")

    # A couple of failures, but not enough to lock.
    for _ in range(MAX_FAILED_ATTEMPTS - 2):
        client.post("/api/v1/auth/login", json={"email": creds["email"], "password": "WrongPassword!"})

    success = client.post(
        "/api/v1/auth/login", json={"email": creds["email"], "password": creds["password"]}
    )
    assert success.status_code == 200

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == creds["email"]).first()
        lockout = db.query(AccountLockout).filter(AccountLockout.user_id == user.id).first()
        assert lockout is not None
        assert lockout.failed_attempts == 0
        assert lockout.locked_until is None
    finally:
        db.close()


def test_successful_login_does_not_duplicate_security_event():
    """86: record_successful_login used to log its own LOGIN_SUCCESS
    SecurityEvent, which would have double-counted every login
    alongside the one Step 82 already added in auth/router.py."""
    creds = _register("no-dup-event", f"No Dup Event Co {uuid.uuid4().hex[:6]}")

    login = client.post("/api/v1/auth/login", json={"email": creds["email"], "password": creds["password"]})
    assert login.status_code == 200

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == creds["email"]).first()
        count = (
            db.query(SecurityEvent)
            .filter(SecurityEvent.event_type == "LOGIN_SUCCESS", SecurityEvent.user_id == user.id)
            .count()
        )
        assert count == 1
    finally:
        db.close()
