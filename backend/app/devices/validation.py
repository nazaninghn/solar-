from datetime import datetime, timedelta, timezone

# 26.35: a lenient but sane window — reject the obviously-wrong cases
# the brief names (a device stuck on a 2020 clock, a clock set days into
# the future) while still tolerating real-world clock drift and network
# delay on genuine telemetry.
MAX_PAST_WINDOW = timedelta(days=7)
MAX_FUTURE_WINDOW = timedelta(days=1)

# 17.26, shared by both the internal polling loop (device_jobs.py) and
# the external telemetry-ingestion endpoint — a device sending garbage
# (e.g. a decimal-point bug reporting -500,000 kW) shouldn't land
# directly in the database from either path.
MAX_PLAUSIBLE_POWER_KW = 100_000


def is_timestamp_plausible(timestamp: datetime) -> bool:
    now = datetime.now(timezone.utc)

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    return now - MAX_PAST_WINDOW <= timestamp <= now + MAX_FUTURE_WINDOW
