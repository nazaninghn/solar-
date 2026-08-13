from datetime import datetime, timezone

# 28.25: "value + timestamp", surfaced as "updated N minutes ago" plus a
# stale flag once too much time has passed. Solar forecasts already had
# their own is_stale flag (19.36's fetch-fails-fall-back-to-last-good
# pattern); this generalizes the same idea to data with no fetch/
# fallback step of its own — electricity pricing here is "how old is
# the last price we were given", not "did a live fetch fail".
DEFAULT_STALE_THRESHOLD_MINUTES = 120


def compute_freshness(
    timestamp: datetime, stale_after_minutes: int = DEFAULT_STALE_THRESHOLD_MINUTES
) -> dict:
    now = datetime.now(timezone.utc)

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    age_minutes = (now - timestamp).total_seconds() / 60

    return {
        "age_minutes": round(age_minutes, 1),
        "is_stale": age_minutes > stale_after_minutes,
    }
