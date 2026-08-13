import time
from collections import defaultdict

from fastapi import HTTPException, status

# 26.34: same in-process sliding-window pattern as app/auth/rate_limit.py
# (single-instance MVP limitation, same as flagged there). Limit is per
# device, not per IP — a device pushing telemetry every few seconds is
# normal; 60/minute comfortably covers that while still bounding a
# malfunctioning or malicious sender.
_TELEMETRY_REQUESTS_PER_MINUTE = 60
_WINDOW_SECONDS = 60.0

_requests: dict[int, list[float]] = defaultdict(list)


def enforce_telemetry_rate_limit(device_id: int) -> None:
    now = time.monotonic()

    recent = [t for t in _requests[device_id] if now - t < _WINDOW_SECONDS]

    if len(recent) >= _TELEMETRY_REQUESTS_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Telemetry rate limit exceeded for this device.",
        )

    recent.append(now)
    _requests[device_id] = recent
