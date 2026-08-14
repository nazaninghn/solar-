import uuid
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.core.security import verify_password
from app.database.session import SessionLocal
from app.main import app
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.modules.auth.data_rights import (
    IdentityVerificationError,
    LastAdminError,
    LegalHoldBlockError,
    delete_own_account,
    export_own_data,
)
from app.modules.compliance.models import LegalHold, Vendor
from app.modules.compliance.service import (
    create_legal_hold,
    create_vendor,
    get_held_organization_ids,
    is_organization_on_hold,
    list_vendors,
    offboard_vendor,
    release_legal_hold,
)
from app.modules.monitoring.models import MonitoringIncident
from app.modules.security.correlation import detect_correlated_security_activity
from app.modules.security.models import SecurityEvent

client = TestClient(app)


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}@pytest.solarflow.com"


def _register_and_login(prefix: str, org_name: str) -> dict:
    """Returns tokens + email/password — never a User instance, since
    that object would be tied to a session this function closes before
    returning. Each test re-queries its own User fresh within its own
    session via _get_user instead of refreshing a detached instance."""
    email = _unique_email(prefix)
    password = "TestPass123!"

    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Pytest Compliance User",
            "organization_name": org_name,
        },
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()

    return {**login, "password": password, "email": email}


def _get_user(db, email: str) -> User:
    return db.query(User).filter(User.email == email).first()


def _add_second_admin(db, organization_id: int, hashed_password: str) -> User:
    admin = User(
        organization_id=organization_id,
        email=_unique_email("second-admin"),
        hashed_password=hashed_password,
        full_name="Second Admin",
        role="COMPANY_ADMIN",
        is_active=True,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(admin)
    db.commit()
    return admin


# --- User data subject rights (79.36-79.40) ---


def test_export_own_data_includes_account_and_organization():
    tokens = _register_and_login("export-test", f"Export Test Co {uuid.uuid4().hex[:6]}")

    db = SessionLocal()
    try:
        user = _get_user(db, tokens["email"])
        export = export_own_data(db, user)

        assert export["account"]["email"] == tokens["email"]
        assert export["organization"]["id"] == user.organization_id
        assert "exported_at" in export
    finally:
        db.close()


def test_delete_own_account_requires_correct_password():
    tokens = _register_and_login("delete-wrongpw", f"Delete WrongPW Co {uuid.uuid4().hex[:6]}")

    db = SessionLocal()
    try:
        user = _get_user(db, tokens["email"])
        raised = False
        try:
            delete_own_account(db, user, "WrongPassword999!")
        except IdentityVerificationError:
            raised = True
        assert raised
    finally:
        db.close()


def test_delete_own_account_blocks_last_admin():
    tokens = _register_and_login("delete-lastadmin", f"Delete LastAdmin Co {uuid.uuid4().hex[:6]}")

    db = SessionLocal()
    try:
        user = _get_user(db, tokens["email"])
        raised = False
        try:
            delete_own_account(db, user, tokens["password"])
        except LastAdminError:
            raised = True
        assert raised

        db.refresh(user)
        assert user.email == tokens["email"]
        assert user.is_active is True
    finally:
        db.close()


def test_delete_own_account_succeeds_with_second_admin_present():
    tokens = _register_and_login("delete-success", f"Delete Success Co {uuid.uuid4().hex[:6]}")

    db = SessionLocal()
    try:
        user = _get_user(db, tokens["email"])
        _add_second_admin(db, user.organization_id, user.hashed_password)

        original_id = user.id
        delete_own_account(db, user, tokens["password"])

        db.refresh(user)
        assert user.is_active is False
        assert user.email != tokens["email"]
        assert user.email.endswith("@anonymized.solarflow.internal")
        assert user.full_name == "Deleted User"
        assert not verify_password(tokens["password"], user.hashed_password)

        active_tokens = (
            db.query(RefreshToken)
            .filter(RefreshToken.user_id == original_id, RefreshToken.revoked_at.is_(None))
            .count()
        )
        assert active_tokens == 0
    finally:
        db.close()


def test_disabled_user_cannot_login_after_self_deletion():
    """End-to-end via the real HTTP endpoint, not just the service
    function — confirms the router wiring, not just the logic."""
    tokens = _register_and_login("delete-http", f"Delete HTTP Co {uuid.uuid4().hex[:6]}")

    db = SessionLocal()
    try:
        user = _get_user(db, tokens["email"])
        _add_second_admin(db, user.organization_id, user.hashed_password)
    finally:
        db.close()

    response = client.post(
        "/api/v1/auth/me/delete",
        json={"password": tokens["password"]},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 204

    login_after = client.post(
        "/api/v1/auth/login", json={"email": tokens["email"], "password": tokens["password"]}
    )
    assert login_after.status_code == 401


# --- Legal hold (79.33) ---


def test_legal_hold_lifecycle():
    tokens = _register_and_login("hold-lifecycle", f"Hold Lifecycle Co {uuid.uuid4().hex[:6]}")

    db = SessionLocal()
    try:
        user = _get_user(db, tokens["email"])
        assert is_organization_on_hold(db, user.organization_id) is False

        hold = create_legal_hold(db, "organization", user.organization_id, "pytest hold", user)
        assert is_organization_on_hold(db, user.organization_id) is True
        assert user.organization_id in get_held_organization_ids(db)

        release_legal_hold(db, hold.id, user)
        assert is_organization_on_hold(db, user.organization_id) is False
    finally:
        db.query(LegalHold).filter(LegalHold.resource_id == user.organization_id).delete()
        db.commit()
        db.close()


def test_legal_hold_blocks_self_deletion():
    tokens = _register_and_login("hold-blocks-delete", f"Hold Blocks Delete Co {uuid.uuid4().hex[:6]}")

    db = SessionLocal()
    try:
        user = _get_user(db, tokens["email"])
        _add_second_admin(db, user.organization_id, user.hashed_password)

        create_legal_hold(db, "organization", user.organization_id, "pytest block test", user)

        raised = False
        try:
            delete_own_account(db, user, tokens["password"])
        except LegalHoldBlockError:
            raised = True
        assert raised

        db.refresh(user)
        assert user.is_active is True
    finally:
        db.query(LegalHold).filter(LegalHold.resource_id == user.organization_id).delete()
        db.commit()
        db.close()


# --- Vendor governance (79.41-79.44) ---


def test_vendor_create_and_offboard():
    db = SessionLocal()
    vendor = None
    try:
        name = f"Pytest Vendor {uuid.uuid4().hex[:8]}"
        vendor = create_vendor(db, name, "testing", "no real data", "LOW", None, False)
        assert vendor.status == "ACTIVE"

        names = {v.name for v in list_vendors(db)}
        assert name in names

        offboarded = offboard_vendor(db, vendor.id)
        assert offboarded.status == "OFFBOARDED"
    finally:
        if vendor is not None:
            db.query(Vendor).filter(Vendor.id == vendor.id).delete()
            db.commit()
        db.close()


# --- Security event correlation (79.29-79.30) ---


def test_brute_force_correlation_opens_incident_once():
    db = SessionLocal()
    test_ip = f"198.51.100.{uuid.uuid4().int % 254 + 1}"
    try:
        now = datetime.now(timezone.utc)
        for _ in range(4):
            db.add(
                SecurityEvent(
                    event_type="LOGIN_FAILED", severity="WARNING", ip_address=test_ip, created_at=now
                )
            )
        db.commit()

        created = detect_correlated_security_activity(db)
        assert created >= 1

        incident = (
            db.query(MonitoringIncident).filter(MonitoringIncident.title.like(f"%{test_ip}%")).first()
        )
        assert incident is not None
        assert incident.service == "security"

        # re-running immediately must not duplicate the open incident
        detect_correlated_security_activity(db)
        duplicate_count = (
            db.query(MonitoringIncident).filter(MonitoringIncident.title.like(f"%{test_ip}%")).count()
        )
        assert duplicate_count == 1
    finally:
        db.query(SecurityEvent).filter(SecurityEvent.ip_address == test_ip).delete()
        db.query(MonitoringIncident).filter(MonitoringIncident.title.like(f"%{test_ip}%")).delete()
        db.commit()
        db.close()


# --- Platform-admin access fix (79.16-79.18) ---


def test_company_admin_cannot_access_platform_admin_endpoints():
    tokens = _register_and_login("platform-fix", f"Platform Fix Co {uuid.uuid4().hex[:6]}")

    response = client.get(
        "/api/v1/admin/organizations",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 403

    response2 = client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response2.status_code == 403
