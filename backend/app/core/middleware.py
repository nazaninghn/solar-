import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.metrics import record_request

logger = logging.getLogger("app.request")

# 28.9: rough, provisional thresholds — good enough to flag something
# worth investigating without pretending to be a tuned SLO.
_EXCELLENT_MS = 200
_GOOD_MS = 500
_WARNING_MS = 1000


def _classify_duration(duration_ms: float) -> str:
    if duration_ms < _EXCELLENT_MS:
        return "excellent"
    if duration_ms < _GOOD_MS:
        return "good"
    if duration_ms < _WARNING_MS:
        return "warning"
    return "slow"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    28.6-28.9: one log line per request, with a request_id a user can
    quote back ("Error code: req_8f71a2c") to find the exact request in
    logs. user_id/organization_id come from request.state, set by
    get_current_user (app/core/dependencies.py) — this middleware runs
    outside the dependency-injection cycle, so it can't resolve who the
    caller is on its own; it can only read back what the route's own
    auth dependency already figured out, after call_next() returns.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        request.state.request_id = request_id

        start = time.monotonic()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.monotonic() - start) * 1000, 1)
            record_request(500, duration_ms, "slow")
            logger.exception(
                "%s %s status=500 duration_ms=%s bucket=slow request_id=%s "
                "user_id=%s organization_id=%s (unhandled exception)",
                request.method,
                request.url.path,
                duration_ms,
                request_id,
                getattr(request.state, "user_id", None),
                getattr(request.state, "organization_id", None),
            )
            raise

        duration_ms = round((time.monotonic() - start) * 1000, 1)
        bucket = _classify_duration(duration_ms)
        record_request(response.status_code, duration_ms, bucket)
        response.headers["X-Request-ID"] = request_id

        log_level = logging.WARNING if bucket in ("warning", "slow") else logging.INFO

        logger.log(
            log_level,
            "%s %s status=%d duration_ms=%s bucket=%s request_id=%s "
            "user_id=%s organization_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            bucket,
            request_id,
            getattr(request.state, "user_id", None),
            getattr(request.state, "organization_id", None),
        )

        return response
