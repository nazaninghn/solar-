import os
import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings

# 82: same in-memory sliding-window shape as app/auth/rate_limit.py and
# app/devices/rate_limit.py — single-instance MVP limitation, consistent
# with those two rather than introducing a third pattern for the same
# problem. Keyed by IP only (not user/org), since middleware runs before
# any auth dependency resolves who the caller is.
_WINDOW_SECONDS = 60.0

_requests: dict[str, list[float]] = defaultdict(list)

# Liveness/readiness checks must never be rate-limited — Render polls
# these on a fixed interval independent of real traffic, and a false
# 429 here would make Render think the whole process is unhealthy.
_EXEMPT_PATHS = {"/health", "/health/ready", "/"}


class GeneralAPIRateLimitMiddleware(BaseHTTPMiddleware):
    """
    82: backstop rate limit for every endpoint that isn't already
    covered by the tighter, purpose-specific login (5/min) or telemetry
    (60/min per device) limits. Before this, a non-login, non-telemetry
    endpoint (e.g. GET /api/v1/factories) had no rate limit of any kind.
    """

    async def dispatch(self, request: Request, call_next):
        if request.url.path in _EXEMPT_PATHS:
            return await call_next(request)

        # 82: the full pytest suite drives every request through
        # TestClient, which reports a single fixed client host
        # ("testclient") for all of them — hundreds of tests sharing one
        # IP would trip this within the suite's own runtime, unlike the
        # login limiter (which survives testing fine because it's keyed
        # by IP+email, and every test uses a unique email). PYTEST_CURRENT_
        # TEST is set by pytest itself for the duration of every test, no
        # extra fixture/config required.
        if "PYTEST_CURRENT_TEST" in os.environ:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"

        if _record_and_check(client_ip):
            _log_rate_limit_hit(client_ip, request.url.path)
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."},
            )

        return await call_next(request)


def _record_and_check(client_ip: str) -> bool:
    """Records one request for `client_ip` and returns True if it just
    tipped the sliding window over the limit. Pulled out of dispatch()
    so the sliding-window logic itself is unit-testable without needing
    a real ASGI request/response cycle."""
    now = time.monotonic()
    recent = [t for t in _requests[client_ip] if now - t < _WINDOW_SECONDS]

    if len(recent) >= settings.API_RATE_LIMIT_PER_MINUTE:
        return True

    recent.append(now)
    _requests[client_ip] = recent
    return False


def _log_rate_limit_hit(client_ip: str, path: str) -> None:
    # A short-lived session opened only on the rare path where the limit
    # is actually hit — not on every request, unlike the DB lookups in
    # get_current_user (which need to run every request regardless).
    from app.database.session import SessionLocal
    from app.modules.security.audit_service import EVENT_RATE_LIMIT_HIT, log_security_event

    db = SessionLocal()
    try:
        log_security_event(
            db,
            event_type=EVENT_RATE_LIMIT_HIT,
            severity="INFO",
            ip_address=client_ip,
            description=f"General API rate limit exceeded for {path}",
        )
    finally:
        db.close()
