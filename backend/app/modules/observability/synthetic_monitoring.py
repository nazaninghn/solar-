"""
STEP 77.53: synthetic monitoring — real outbound HTTP requests back to
this same process, not in-process function calls, so a failure to
accept connections at all (the process is wedged, the port isn't
bound, a reverse proxy misconfiguration) is actually caught the way an
internal health-check call never would be.

Scoped to the two unauthenticated endpoints (liveness, readiness) —
77.53 also mentions a login flow and a critical transaction, but
exercising those synthetically needs either a dedicated
synthetic-monitoring service account or a fabricated auth token, both
of which are a real security-surface decision (a standing credential
whose only job is being probed every few minutes) that shouldn't be
made silently inside a monitoring job. Left as a flagged follow-up,
not built here.
"""

import time
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.observability.system_health import update_source_health

_CHECKS = (
    ("synthetic_liveness", "/health"),
    ("synthetic_readiness", "/health/ready"),
)
_TIMEOUT_SECONDS = 5.0


async def run_synthetic_checks(db: Session) -> list[dict]:
    results = []

    async with httpx.AsyncClient(
        base_url=settings.SYNTHETIC_MONITORING_BASE_URL, timeout=_TIMEOUT_SECONDS
    ) as client:
        for name, path in _CHECKS:
            start = time.monotonic()
            success = False
            error_message = None

            try:
                response = await client.get(path)
                latency_ms = round((time.monotonic() - start) * 1000, 1)
                success = response.status_code == 200
                if not success:
                    error_message = f"HTTP {response.status_code}"
            except Exception as error:
                latency_ms = round((time.monotonic() - start) * 1000, 1)
                error_message = str(error)[:500]

            source = update_source_health(db, name, success, latency_ms, error_message)
            source.type = "synthetic"
            db.commit()
            results.append(
                {
                    "name": name,
                    "path": path,
                    "success": success,
                    "latency_ms": latency_ms,
                    "error": error_message,
                    "checked_at": datetime.now(timezone.utc).isoformat(),
                }
            )

    return results
