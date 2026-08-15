"""
STEP 89: real, runnable smoke test — exercises exactly the steps
docs/release-process.md's Smoke Test Script lists, plus a real login ->
core-workflow round trip, against any base URL (local dev or the actual
production URL after a deploy). Prints a clear PASS/FAIL per step and a
final summary; exits non-zero if anything failed, so it's usable as a
post-deploy gate, not just a manual checklist.

Usage:
    python scripts/smoke_test.py --base-url https://your-service.onrender.com
"""

import argparse
import sys
import uuid

import httpx


def check(name: str, condition: bool, detail: str = "") -> bool:
    status = "PASS" if condition else "FAIL"
    line = f"[{status}] {name}"
    if detail:
        line += f" — {detail}"
    print(line)
    return condition


def run(base_url: str) -> bool:
    results = []

    with httpx.Client(base_url=base_url, timeout=15.0) as client:
        # 1. Application responds
        try:
            root = client.get("/")
            results.append(check("Application responds", root.status_code == 200, f"status={root.status_code}"))
        except httpx.HTTPError as error:
            results.append(check("Application responds", False, str(error)))
            print("\nApplication is unreachable — stopping here, nothing else can be tested.")
            return False

        # 2. Liveness
        health = client.get("/health")
        results.append(check("GET /health -> 200", health.status_code == 200))

        # 3. Readiness (real DB check)
        ready = client.get("/health/ready")
        ready_ok = ready.status_code == 200 and ready.json().get("status") == "ready"
        results.append(check("GET /health/ready -> ready", ready_ok, ready.text))

        # 4. Swagger docs accessible
        docs = client.get("/docs")
        results.append(check("Swagger /docs accessible", docs.status_code == 200))

        # 5. Auth endpoint validates input (422, not 500) — the exact
        # check docs/release-process.md's smoke test script specifies.
        bad_login = client.post("/api/v1/auth/login", json={})
        results.append(
            check(
                "POST /api/v1/auth/login with empty body -> 422, not 500",
                bad_login.status_code == 422,
                f"status={bad_login.status_code}",
            )
        )

        # 6. Real register -> login -> core workflow round trip.
        suffix = uuid.uuid4().hex[:8]
        email = f"smoketest-{suffix}@pytest.solarflow.com"
        password = "SmokeTest123!"

        register = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Smoke Test",
                "organization_name": f"Smoke Test Co {suffix}",
            },
        )
        results.append(check("Register succeeds", register.status_code == 201, f"status={register.status_code}"))

        login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        login_ok = login.status_code == 200 and "access_token" in login.json()
        results.append(check("Login succeeds and returns a token", login_ok))

        if login_ok:
            token = login.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            me = client.get("/api/v1/auth/me", headers=headers)
            results.append(check("Authenticated /me works", me.status_code == 200))

            factories = client.get("/api/v1/factories", headers=headers)
            results.append(
                check("Dashboard-equivalent (factory list) responds", factories.status_code == 200)
            )

            create = client.post(
                "/api/v1/factories", headers=headers, json={"name": "Smoke Test Factory", "timezone": "UTC"}
            )
            results.append(check("Core workflow: create a factory", create.status_code == 201))
        else:
            results.append(check("Authenticated /me works", False, "skipped, login failed"))
            results.append(check("Dashboard-equivalent (factory list) responds", False, "skipped, login failed"))
            results.append(check("Core workflow: create a factory", False, "skipped, login failed"))

    all_passed = all(results)
    print(f"\n{sum(results)}/{len(results)} checks passed.")
    return all_passed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    passed = run(args.base_url)
    sys.exit(0 if passed else 1)
