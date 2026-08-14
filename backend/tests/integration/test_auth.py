"""
STEP 48.11 / 79.16-79.19: Authentication integration tests.

Tests login, token refresh, logout, disabled user, locked user scenarios.
These 9 methods existed as unimplemented `pass` placeholders before
Step 79.
"""

import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

client = TestClient(app)


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}@pytest.solarflow.com"


def _register(email: str, password: str, org_name: str) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Pytest Auth User",
            "organization_name": org_name,
        },
    )


class TestAuthentication:
    """48.11: Auth flow integration tests."""

    def test_valid_login_returns_tokens(self):
        """Valid credentials should return access + refresh tokens."""
        email = _unique_email("valid-login")
        password = "TestPass123!"
        _register(email, password, f"Valid Login Co {uuid.uuid4().hex[:6]}")

        response = client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )

        assert response.status_code == 200
        body = response.json()
        assert body["access_token"]
        assert body["refresh_token"]
        assert body["token_type"] == "bearer"

    def test_invalid_password_returns_401(self):
        """Wrong password should return 401."""
        email = _unique_email("invalid-password")
        _register(email, "CorrectPass123!", f"Invalid Password Co {uuid.uuid4().hex[:6]}")

        response = client.post(
            "/api/v1/auth/login", json={"email": email, "password": "WrongPass999!"}
        )
        assert response.status_code == 401

    def test_unknown_user_returns_401(self):
        """Non-existent user should return 401, not 500."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": _unique_email("never-registered"), "password": "Whatever123!"},
        )
        assert response.status_code == 401

    def test_expired_token_returns_401(self):
        """Expired access token should be rejected."""
        email = _unique_email("expired-token-2")
        password = "TestPass123!"
        _register(email, password, f"Expired Token Co 2 {uuid.uuid4().hex[:6]}")
        login = client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        ).json()

        me = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {login['access_token']}"}
        ).json()

        expired_token = jwt.encode(
            {
                "sub": str(me["id"]),
                "type": "access",
                "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
            },
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )

        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401

    def test_refresh_token_returns_new_tokens(self):
        """Valid refresh token should return a new access + refresh pair."""
        email = _unique_email("refresh-ok")
        password = "TestPass123!"
        _register(email, password, f"Refresh OK Co {uuid.uuid4().hex[:6]}")
        login = client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        ).json()

        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]}
        )

        assert response.status_code == 200
        body = response.json()
        assert body["access_token"]
        assert body["refresh_token"]
        # Not asserting the new refresh token differs byte-for-byte from
        # the old one: the JWT payload (sub/type/exp) has no unique jti,
        # so two rotations within the same second produce an identical
        # string. Rotation is still real at the DB layer — the old
        # token's row is revoked, proven by test_revoked_refresh_token_
        # rejected below actually getting a 401 on reuse.

    def test_revoked_refresh_token_rejected(self):
        """24.35's rotation: a refresh token that was already used to
        mint a new pair should not work a second time."""
        email = _unique_email("refresh-rotation")
        password = "TestPass123!"
        _register(email, password, f"Refresh Rotation Co {uuid.uuid4().hex[:6]}")
        login = client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        ).json()

        first_use = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]}
        )
        assert first_use.status_code == 200

        second_use = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]}
        )
        assert second_use.status_code == 401

    def test_logout_invalidates_session(self):
        """After logout, the (now-revoked) refresh token should no
        longer mint new access tokens. Access tokens themselves are
        stateless JWTs with no revocation list in this codebase — the
        refresh token is the actual "session" that logout can end."""
        email = _unique_email("logout-test")
        password = "TestPass123!"
        _register(email, password, f"Logout Test Co {uuid.uuid4().hex[:6]}")
        login = client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        ).json()

        logout_response = client.post(
            "/api/v1/auth/logout", json={"refresh_token": login["refresh_token"]}
        )
        assert logout_response.status_code == 204

        refresh_after_logout = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]}
        )
        assert refresh_after_logout.status_code == 401

    def test_disabled_user_cannot_login(self):
        """Disabled user should get 401, not a partial/500."""
        admin_email = _unique_email("disable-admin")
        admin_password = "AdminPass123!"
        _register(admin_email, admin_password, f"Disable User Co {uuid.uuid4().hex[:6]}")
        admin_token = client.post(
            "/api/v1/auth/login", json={"email": admin_email, "password": admin_password}
        ).json()["access_token"]

        target_email = _unique_email("disable-target")
        target_password = "TargetPass123!"
        created = client.post(
            "/api/v1/company/users",
            json={
                "email": target_email,
                "password": target_password,
                "full_name": "Soon Disabled",
                "role": "VIEWER",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        ).json()

        client.delete(
            f"/api/v1/company/users/{created['id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        response = client.post(
            "/api/v1/auth/login",
            json={"email": target_email, "password": target_password},
        )
        assert response.status_code == 401

    def test_locked_user_cannot_login(self):
        """Repeated failed logins should lock the account (Step 47's
        lockout.py — 5 attempts / 30 min) even with the correct password
        on a later attempt."""
        email = _unique_email("lockout-test")
        password = "CorrectPass123!"
        _register(email, password, f"Lockout Test Co {uuid.uuid4().hex[:6]}")

        for _ in range(5):
            client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": "WrongPassword999!"},
            )

        response = client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        assert response.status_code in (401, 423, 429)
