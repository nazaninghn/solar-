"""
STEP 84: a real load-testing script for a single Render web-service
instance — not a mock, not fabricated numbers. Run it against a live
`uvicorn app.main:app` process (see usage below) to get actual P50/P95/P99
latency, throughput, and error-rate numbers for the critical user
journeys this platform actually has: login, and the dashboard-style
reads a logged-in user does most (factory list, system metrics).

Deliberately NOT locust/k6 — this project has zero load-testing
dependencies today, and httpx (already in requirements.txt for the
weather client) is enough to drive concurrent async requests without
adding a new dependency for a single admin-run script.

Usage:
    python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
    python scripts/load_test.py --base-url http://127.0.0.1:8000

Every number this script prints is measured from real HTTP round trips
against a real running server and a real database — nothing here is
estimated or hardcoded.
"""

import argparse
import asyncio
import statistics
import time
import uuid
from dataclasses import dataclass, field

import httpx


@dataclass
class ScenarioResult:
    name: str
    durations_ms: list[float] = field(default_factory=list)
    status_codes: dict[int, int] = field(default_factory=dict)
    errors: int = 0
    wall_seconds: float = 0.0

    def record(self, duration_ms: float, status_code: int | None) -> None:
        self.durations_ms.append(duration_ms)
        if status_code is None:
            self.errors += 1
        else:
            self.status_codes[status_code] = self.status_codes.get(status_code, 0) + 1

    def percentile(self, p: float) -> float:
        if not self.durations_ms:
            return 0.0
        data = sorted(self.durations_ms)
        idx = min(int(len(data) * p), len(data) - 1)
        return data[idx]

    def report(self, wall_seconds: float) -> str:
        total = len(self.durations_ms)
        error_rate = self.errors / total * 100 if total else 0.0
        throughput = total / wall_seconds if wall_seconds else 0.0
        return (
            f"[{self.name}] requests={total} wall={wall_seconds:.1f}s "
            f"throughput={throughput:.1f} req/s error_rate={error_rate:.1f}% "
            f"p50={self.percentile(0.50):.0f}ms p95={self.percentile(0.95):.0f}ms "
            f"p99={self.percentile(0.99):.0f}ms "
            f"status_codes={dict(sorted(self.status_codes.items()))}"
        )


async def _register_test_users(client: httpx.AsyncClient, count: int) -> list[dict]:
    """Real registrations against the real DB — same endpoint any real
    signup goes through, so the login journey below is authentic."""
    users = []
    for i in range(count):
        suffix = uuid.uuid4().hex[:8]
        email = f"loadtest-{suffix}@pytest.solarflow.com"
        password = "LoadTest123!"
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": f"Load Test User {i}",
                "organization_name": f"Load Test Org {suffix}",
            },
        )
        users.append({"email": email, "password": password})
    return users


async def _login(client: httpx.AsyncClient, user: dict) -> str | None:
    response = await client.post(
        "/api/v1/auth/login", json={"email": user["email"], "password": user["password"]}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


async def _steady_state_worker(
    client: httpx.AsyncClient,
    token: str,
    result: ScenarioResult,
    stop_at: float,
) -> None:
    headers = {"Authorization": f"Bearer {token}"}
    while time.monotonic() < stop_at:
        start = time.monotonic()
        try:
            response = await client.get("/api/v1/factories", headers=headers)
            status_code = response.status_code
        except httpx.HTTPError:
            status_code = None
        duration_ms = (time.monotonic() - start) * 1000
        result.record(duration_ms, status_code)


async def run_dashboard_read_scenario(
    base_url: str, concurrency: int, duration_seconds: float, label: str
) -> ScenarioResult:
    """Simulates `concurrency` logged-in users repeatedly hitting the
    factory-list endpoint for `duration_seconds` — this project's
    closest real analogue to a dashboard read, per docs/operations/
    scalability.md's own "Dashboard <500ms" target."""
    result = ScenarioResult(name=label)

    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        users = await _register_test_users(client, concurrency)
        tokens = await asyncio.gather(*[_login(client, u) for u in users])
        tokens = [t for t in tokens if t is not None]

        if not tokens:
            result.errors = concurrency
            return result

        start_wall = time.monotonic()
        stop_at = start_wall + duration_seconds
        await asyncio.gather(
            *[_steady_state_worker(client, token, result, stop_at) for token in tokens]
        )
        result.wall_seconds = time.monotonic() - start_wall

    return result


async def run_login_scenario(base_url: str, concurrency: int, label: str) -> ScenarioResult:
    """Login is rate-limited (5/min per IP+email, Step 24) by design —
    this scenario registers `concurrency` distinct users and logs each
    in exactly once, concurrently, which is the realistic shape of a
    login burst (many different users, not one user retrying)."""
    result = ScenarioResult(name=label)

    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        users = await _register_test_users(client, concurrency)

        async def _timed_login(user: dict) -> None:
            start = time.monotonic()
            try:
                response = await client.post(
                    "/api/v1/auth/login",
                    json={"email": user["email"], "password": user["password"]},
                )
                status_code = response.status_code
            except httpx.HTTPError:
                status_code = None
            result.record((time.monotonic() - start) * 1000, status_code)

        start_wall = time.monotonic()
        await asyncio.gather(*[_timed_login(u) for u in users])
        result.wall_seconds = time.monotonic() - start_wall

    return result


async def main(base_url: str) -> None:
    print(f"Load testing {base_url} — real HTTP requests against a live server + real DB.\n")

    login_normal = await run_login_scenario(base_url, concurrency=10, label="login (normal, 10 concurrent signups+logins)")
    print(login_normal.report(login_normal.wall_seconds))

    login_peak = await run_login_scenario(base_url, concurrency=50, label="login (peak, 50 concurrent signups+logins)")
    print(login_peak.report(login_peak.wall_seconds))

    dashboard_normal = await run_dashboard_read_scenario(
        base_url, concurrency=10, duration_seconds=15, label="dashboard read (normal, 10 users x 15s)"
    )
    print(dashboard_normal.report(dashboard_normal.wall_seconds))

    dashboard_peak = await run_dashboard_read_scenario(
        base_url, concurrency=50, duration_seconds=15, label="dashboard read (peak, 50 users x 15s)"
    )
    print(dashboard_peak.report(dashboard_peak.wall_seconds))

    dashboard_stress = await run_dashboard_read_scenario(
        base_url, concurrency=150, duration_seconds=15, label="dashboard read (stress, 150 users x 15s)"
    )
    print(dashboard_stress.report(dashboard_stress.wall_seconds))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    asyncio.run(main(args.base_url))
