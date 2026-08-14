from datetime import datetime, timezone

# 31.16-31.17: same 15-minute threshold device_health_jobs.py already
# uses to mark a device OFFLINE — reused here so the freshness
# component of the health score and the persisted OFFLINE status agree
# with each other, instead of two independently-tuned thresholds
# drifting apart over time.
OFFLINE_THRESHOLD_MINUTES = 15

_STATUS_SCORES = {
    "ONLINE": 100.0,
    "WARNING": 60.0,
    "UNKNOWN": 40.0,
    "ERROR": 10.0,
    "OFFLINE": 0.0,
}


def calculate_device_health_score(device) -> dict:
    """
    31.17: a single 0-100 score blending data freshness, connection/
    status reliability, and recent error rate — MVP weights (0.4/0.4/
    0.2), tunable once there's real operational data to calibrate
    against.
    """
    now = datetime.now(timezone.utc)

    if device.last_seen_at is None:
        freshness_score = 0.0
        age_minutes = None
    else:
        last_seen = device.last_seen_at
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)

        age_minutes = (now - last_seen).total_seconds() / 60
        freshness_score = max(
            0.0, 100.0 - (age_minutes / OFFLINE_THRESHOLD_MINUTES) * 100
        )

    status_score = _STATUS_SCORES.get(device.status, 40.0)

    # Each consecutive failure knocks 20 points off, floor at 0 — a
    # device on its 5th+ straight failed poll scores 0 here regardless
    # of how fresh its last *successful* reading was.
    error_score = max(0.0, 100.0 - device.consecutive_error_count * 20.0)

    health_score = round(
        freshness_score * 0.4 + status_score * 0.4 + error_score * 0.2, 1
    )

    return {
        "health_score": health_score,
        "freshness_score": round(freshness_score, 1),
        "status_score": status_score,
        "error_score": error_score,
        "age_minutes": round(age_minutes, 1) if age_minutes is not None else None,
        "consecutive_error_count": device.consecutive_error_count,
        "last_error_message": device.last_error_message,
    }
