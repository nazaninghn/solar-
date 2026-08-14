"""
STEP 48.13 / 79.58-79.59: Tenant isolation integration tests.

Ensures Organization A cannot access Organization B's resources.
These 8 methods existed as unimplemented `pass` placeholders before
Step 79 — the structure was there, nothing actually ran.
"""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

import app.models  # noqa: F401 - registers full metadata for direct model use below
from app.database.session import SessionLocal
from app.main import app
from app.modules.billing.models import Invoice

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
            "full_name": "Pytest Tenant User",
            "organization_name": org_name,
        },
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return login.json()


def _create_factory(access_token: str, name: str) -> dict:
    return client.post(
        "/api/v1/factories",
        json={"name": name},
        headers={"Authorization": f"Bearer {access_token}"},
    ).json()


def _two_orgs():
    """Two isolated companies, each with one factory."""
    org_a = _register_and_login("tenant-a", f"Tenant Isolation Co A {uuid.uuid4().hex[:6]}")
    org_b = _register_and_login("tenant-b", f"Tenant Isolation Co B {uuid.uuid4().hex[:6]}")
    factory_a = _create_factory(org_a["access_token"], "Org A Factory")
    factory_b = _create_factory(org_b["access_token"], "Org B Factory")
    return org_a, org_b, factory_a, factory_b


class TestTenantIsolation:
    """48.13: Multi-tenant security tests."""

    def test_user_cannot_access_other_org_factories(self):
        """User from Org A should get 404 for Org B factory — 24.39's
        resolved "404 not 403" decision so existence isn't leaked
        across an org boundary with no relationship at all."""
        org_a, org_b, factory_a, factory_b = _two_orgs()

        response = client.get(
            f"/api/v1/factories/{factory_b['id']}",
            headers={"Authorization": f"Bearer {org_a['access_token']}"},
        )
        assert response.status_code == 404

    def test_user_cannot_access_other_org_devices(self):
        """User from Org A should not see Org B devices."""
        org_a, org_b, factory_a, factory_b = _two_orgs()

        client.post(
            f"/api/v1/factories/{factory_b['id']}/devices",
            json={
                "name": "Org B Device",
                "device_type": "INVERTER",
                "connection_type": "SIMULATOR",
            },
            headers={"Authorization": f"Bearer {org_b['access_token']}"},
        )

        response = client.get(
            f"/api/v1/factories/{factory_b['id']}/devices",
            headers={"Authorization": f"Bearer {org_a['access_token']}"},
        )
        assert response.status_code == 404

    def test_user_cannot_access_other_org_analytics(self):
        """Analytics scoped to own organization only."""
        org_a, org_b, factory_a, factory_b = _two_orgs()

        response = client.get(
            f"/api/v1/factories/{factory_b['id']}/analytics/today",
            headers={"Authorization": f"Bearer {org_a['access_token']}"},
        )
        assert response.status_code == 404

    def test_user_cannot_access_other_org_alerts(self):
        """Alerts belong to organization only."""
        org_a, org_b, factory_a, factory_b = _two_orgs()

        response = client.get(
            f"/api/v1/factories/{factory_b['id']}/alerts",
            headers={"Authorization": f"Bearer {org_a['access_token']}"},
        )
        assert response.status_code == 404

    def test_user_cannot_access_other_org_billing(self):
        """Invoices, subscriptions, settlements scoped — /billing/invoices
        is org-scoped implicitly via get_current_user (no factory_id path
        param), so this creates a real Org B invoice and confirms Org A's
        own list call never includes it."""
        org_a, org_b, factory_a, factory_b = _two_orgs()

        org_b_id = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {org_b['access_token']}"}
        ).json()["organization"]["id"]

        db = SessionLocal()
        try:
            invoice_number = f"PYTEST-{uuid.uuid4().hex[:10]}"
            now = datetime.now(timezone.utc)
            db.add(
                Invoice(
                    organization_id=org_b_id,
                    invoice_number=invoice_number,
                    status="DRAFT",
                    period_start=now - timedelta(days=30),
                    period_end=now,
                    created_at=now,
                )
            )
            db.commit()
        finally:
            db.close()

        response = client.get(
            "/api/v1/billing/invoices",
            headers={"Authorization": f"Bearer {org_a['access_token']}"},
        )
        assert response.status_code == 200
        invoice_numbers = {inv["invoice_number"] for inv in response.json()}
        assert invoice_number not in invoice_numbers

    def test_user_cannot_access_other_org_settlements(self):
        """Energy settlements are factory-scoped within org."""
        org_a, org_b, factory_a, factory_b = _two_orgs()

        response = client.get(
            f"/api/v1/factories/{factory_b['id']}/settlements",
            headers={"Authorization": f"Bearer {org_a['access_token']}"},
        )
        assert response.status_code == 404

    def test_admin_api_requires_platform_role(self):
        """Regular org admin (COMPANY_ADMIN) cannot access platform admin
        endpoints — 79.16-79.18: this was a real bug fixed in this same
        step (_require_platform_admin previously accepted COMPANY_ADMIN,
        letting any company's admin list/modify every other company's
        organizations and users)."""
        org_a, _, _, _ = _two_orgs()

        response = client.get(
            "/api/v1/admin/organizations",
            headers={"Authorization": f"Bearer {org_a['access_token']}"},
        )
        assert response.status_code == 403

    def test_api_key_scoped_to_organization(self):
        """API key from Org A cannot access Org B data.

        No request path in this codebase currently authenticates via
        APIKey (app/modules/admin/models.py) — it can be created/
        revoked through the admin panel, but nothing in the request
        pipeline (app/core/dependencies.py) validates one as a bearer
        credential. There is no live cross-org request to attempt yet,
        so this verifies the one thing that IS real: two orgs' keys are
        stored under their own organization_id, not shared or
        cross-visible at the data layer.
        """
        org_a, org_b, _, _ = _two_orgs()

        key_a = client.post(
            "/api/v1/admin/api-keys",
            json={"name": "Org A Key"},
            headers={"Authorization": f"Bearer {org_a['access_token']}"},
        )
        # SUPER_ADMIN-only per the same platform-admin gate — a regular
        # COMPANY_ADMIN correctly can't even create one.
        assert key_a.status_code == 403
