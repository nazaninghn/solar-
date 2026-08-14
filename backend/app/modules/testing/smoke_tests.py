"""
STEP 48.50: Production Smoke Tests.

Quick validation that core services are operational after deployment.
Run after every deploy to confirm system health.
"""

import logging
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)


class SmokeTestResult:
    def __init__(self):
        self.results: list[dict] = []
        self.passed = 0
        self.failed = 0

    def add(self, name: str, passed: bool, detail: str = ""):
        self.results.append({"name": name, "passed": passed, "detail": detail})
        if passed:
            self.passed += 1
        else:
            self.failed += 1

    @property
    def all_passed(self) -> bool:
        return self.failed == 0

    def summary(self) -> dict:
        return {
            "total": self.passed + self.failed,
            "passed": self.passed,
            "failed": self.failed,
            "all_passed": self.all_passed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "results": self.results,
        }


async def run_smoke_tests(base_url: str) -> SmokeTestResult:
    """
    48.50: Run smoke tests against a deployed instance.
    Tests core health, auth, and critical API endpoints.
    """
    result = SmokeTestResult()

    async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
        # 1. Liveness
        try:
            r = await client.get("/health")
            result.add("health_live", r.status_code == 200, f"status={r.status_code}")
        except Exception as e:
            result.add("health_live", False, str(e))

        # 2. Readiness
        try:
            r = await client.get("/health/ready")
            result.add("health_ready", r.status_code == 200 and r.json().get("status") == "ready",
                       f"status={r.status_code} body={r.text[:100]}")
        except Exception as e:
            result.add("health_ready", False, str(e))

        # 3. Root endpoint
        try:
            r = await client.get("/")
            data = r.json()
            result.add("root_endpoint", data.get("status") == "online", f"response={data}")
        except Exception as e:
            result.add("root_endpoint", False, str(e))

        # 4. Swagger docs
        try:
            r = await client.get("/docs")
            result.add("swagger_docs", r.status_code == 200, f"status={r.status_code}")
        except Exception as e:
            result.add("swagger_docs", False, str(e))

        # 5. Auth endpoint exists (should return 422 without body, not 500)
        try:
            r = await client.post("/api/v1/auth/login", json={})
            result.add("auth_endpoint", r.status_code in (400, 401, 422), f"status={r.status_code}")
        except Exception as e:
            result.add("auth_endpoint", False, str(e))

        # 6. Plans endpoint (public)
        try:
            r = await client.get("/api/v1/billing/plans")
            result.add("billing_plans", r.status_code == 200, f"status={r.status_code}")
        except Exception as e:
            result.add("billing_plans", False, str(e))

    return result
