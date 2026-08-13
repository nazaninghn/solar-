import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

client = TestClient(app)


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}@pytest.solarflow.com"


def _register_and_login(email: str, password: str, org_name: str) -> dict:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Pytest User",
            "organization_name": org_name,
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )

    return response.json()


def _create_factory(access_token: str, name: str) -> dict:
    response = client.post(
        "/api/v1/factories",
        json={"name": name},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    return response.json()


def test_login_success():
    """Test 1 (24.39): valid credentials -> 200 with access + refresh tokens."""
    email = _unique_email("login-success")
    password = "TestPass123!"

    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Pytest User",
            "organization_name": "Login Success Co",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password():
    """Test 2 (24.39): valid email, wrong password -> 401."""
    email = _unique_email("wrong-password")

    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "CorrectPass123!",
            "full_name": "Pytest User",
            "organization_name": "Wrong Password Co",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPassword999!"},
    )

    assert response.status_code == 401


def test_expired_token_rejected():
    """Test 3 (24.39): a syntactically valid but expired access token -> 401."""
    email = _unique_email("expired-token")
    tokens = _register_and_login(email, "TestPass123!", "Expired Token Co")

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    user_id = me_response.json()["id"]

    expired_token = jwt.encode(
        {
            "sub": str(user_id),
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
        },
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401


def test_company_isolation_returns_404():
    """Test 4 (24.39): a user from Company A hitting a Company B factory
    gets 404, not 403 — resolved explicitly with the user during Step 24:
    a 403 would leak that the factory_id exists to a caller with zero
    relationship to that company at all."""
    tokens_a = _register_and_login(
        _unique_email("company-a"), "TestPass123!", "Isolation Co A"
    )
    tokens_b = _register_and_login(
        _unique_email("company-b"), "TestPass123!", "Isolation Co B"
    )

    factory_b = _create_factory(tokens_b["access_token"], "Company B Factory")

    response = client.get(
        f"/api/v1/factories/{factory_b['id']}",
        headers={"Authorization": f"Bearer {tokens_a['access_token']}"},
    )

    assert response.status_code == 404


def test_same_company_unassigned_factory_returns_403():
    """Test 5 (24.39): a non-admin user in the SAME company as a factory,
    but not individually assigned to it via user_factory_access, gets
    403 — the company already has a legitimate relationship to the
    factory, so unlike Test 4 its existence isn't secret from this user."""
    admin_tokens = _register_and_login(
        _unique_email("factory-access-admin"), "AdminPass123!", "Factory Access Co"
    )
    admin_token = admin_tokens["access_token"]

    factory = _create_factory(admin_token, "Unassigned Factory")

    viewer_email = _unique_email("factory-access-viewer")
    client.post(
        "/api/v1/company/users",
        json={
            "email": viewer_email,
            "password": "ViewerPass123!",
            "full_name": "Scoped Viewer",
            "role": "VIEWER",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    viewer_login = client.post(
        "/api/v1/auth/login",
        json={"email": viewer_email, "password": "ViewerPass123!"},
    )
    viewer_token = viewer_login.json()["access_token"]

    response = client.get(
        f"/api/v1/factories/{factory['id']}",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert response.status_code == 403


def test_viewer_forbidden_from_management_actions():
    """Test 6 (24.39): VIEWER has no MANAGE_* permission — creating a
    factory must be rejected with 403, not silently allowed."""
    admin_tokens = _register_and_login(
        _unique_email("viewer-forbidden-admin"), "AdminPass123!", "Viewer Forbidden Co"
    )
    admin_token = admin_tokens["access_token"]

    viewer_email = _unique_email("viewer-forbidden")
    client.post(
        "/api/v1/company/users",
        json={
            "email": viewer_email,
            "password": "ViewerPass123!",
            "full_name": "Forbidden Viewer",
            "role": "VIEWER",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    viewer_login = client.post(
        "/api/v1/auth/login",
        json={"email": viewer_email, "password": "ViewerPass123!"},
    )
    viewer_token = viewer_login.json()["access_token"]

    response = client.post(
        "/api/v1/factories",
        json={"name": "Viewer Should Not Create This"},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert response.status_code == 403


def test_financial_manager_scoped_access():
    """Test 7 (24.39): FINANCIAL_MANAGER can reach factories it's
    assigned to (VIEW_* permissions) but is blocked from admin-only
    actions like managing users or factory settings (no MANAGE_USERS /
    MANAGE_FACTORY_SETTINGS in its row of the permission matrix)."""
    admin_tokens = _register_and_login(
        _unique_email("fm-scoped-admin"), "AdminPass123!", "Financial Scoped Co"
    )
    admin_token = admin_tokens["access_token"]

    factory = _create_factory(admin_token, "FM Scoped Factory")

    fm_email = _unique_email("fm-scoped")
    fm_user = client.post(
        "/api/v1/company/users",
        json={
            "email": fm_email,
            "password": "FmPass123456!",
            "full_name": "Scoped Financial Manager",
            "role": "FINANCIAL_MANAGER",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()

    client.post(
        f"/api/v1/company/users/{fm_user['id']}/factories",
        json={"factory_id": factory["id"]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    fm_login = client.post(
        "/api/v1/auth/login",
        json={"email": fm_email, "password": "FmPass123456!"},
    )
    fm_token = fm_login.json()["access_token"]

    # Allowed: read access to its assigned factory.
    read_response = client.get(
        f"/api/v1/factories/{factory['id']}",
        headers={"Authorization": f"Bearer {fm_token}"},
    )
    assert read_response.status_code == 200

    # Forbidden: no MANAGE_FACTORY_SETTINGS.
    update_response = client.patch(
        f"/api/v1/factories/{factory['id']}",
        json={"name": "Renamed By FM"},
        headers={"Authorization": f"Bearer {fm_token}"},
    )
    assert update_response.status_code == 403

    # Forbidden: no MANAGE_USERS.
    users_response = client.get(
        "/api/v1/company/users",
        headers={"Authorization": f"Bearer {fm_token}"},
    )
    assert users_response.status_code == 403
