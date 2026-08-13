import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

# 24.35: in-memory sliding window, single-instance MVP limitation —
# same category as the APScheduler jobs (Step 13): fine for one process,
# would need a shared store (Redis) behind a load balancer with multiple
# API instances.
_LOGIN_ATTEMPTS_PER_MINUTE = 5
_WINDOW_SECONDS = 60.0

_attempts: dict[str, list[float]] = defaultdict(list)


def enforce_login_rate_limit(request: Request, email: str) -> None:
    key = f"{request.client.host if request.client else 'unknown'}:{email.lower()}"
    now = time.monotonic()

    recent = [t for t in _attempts[key] if now - t < _WINDOW_SECONDS]

    if len(recent) >= _LOGIN_ATTEMPTS_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again in a minute.",
        )

    recent.append(now)
    _attempts[key] = recent
