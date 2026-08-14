"""
STEP 77.56-77.57: baseline -> deviation -> flag. DataAnomaly (Step 50)
has existed as a table with no writer — this is real detection logic
for it, statistical-process-control style (mean +/- N*stddev), not a
placeholder.

Scoped to EnergyDaily (already-aggregated, low-volume, long-retained)
rather than raw device telemetry — a factory's day-over-day solar/
consumption pattern is both a meaningful business signal (77.55 — "is
something actually wrong" vs. "is one sensor noisy") and cheap to
compute a rolling baseline over.
"""

import statistics
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.jobs.common import get_all_factories
from app.models.energy_daily import EnergyDaily
from app.modules.data_integrity.models import DataAnomaly

BASELINE_WINDOW_DAYS = 30
MIN_BASELINE_SAMPLES = 7
# 77.57: "Expected Range -> Actual Value -> Deviation" — 2.5 standard
# deviations is a standard, moderately conservative statistical-
# process-control threshold (roughly the top/bottom ~0.6% under a
# normal distribution), tunable later same as every other system
# default this project has introduced (BATTERY_DEGRADATION_RATE,
# MAX_PLAUSIBLE_POWER_KW).
DEVIATION_THRESHOLD_STDDEVS = 2.5

_METRICS = ("solar_kwh", "consumption_kwh")


def _severity_for_deviation(stddevs_away: float) -> str:
    if stddevs_away >= 4:
        return "CRITICAL"
    if stddevs_away >= 3:
        return "HIGH"
    return "MEDIUM"


def detect_energy_anomalies(db: Session, as_of: date | None = None) -> int:
    """Returns the number of new DataAnomaly rows written."""
    as_of = as_of or (datetime.now(timezone.utc).date() - timedelta(days=1))
    window_start = as_of - timedelta(days=BASELINE_WINDOW_DAYS)

    created = 0

    for factory in get_all_factories(db):
        rows = db.scalars(
            select(EnergyDaily)
            .where(
                EnergyDaily.factory_id == factory.id,
                EnergyDaily.date >= window_start,
                EnergyDaily.date <= as_of,
            )
            .order_by(EnergyDaily.date)
        ).all()

        today_row = next((r for r in rows if r.date == as_of), None)
        if today_row is None:
            continue

        baseline_rows = [r for r in rows if r.date != as_of]
        if len(baseline_rows) < MIN_BASELINE_SAMPLES:
            continue

        for metric in _METRICS:
            baseline_values = [getattr(r, metric) for r in baseline_rows]
            mean = statistics.mean(baseline_values)
            stddev = statistics.pstdev(baseline_values)

            if stddev == 0:
                continue

            actual_value = getattr(today_row, metric)
            stddevs_away = abs(actual_value - mean) / stddev

            if stddevs_away < DEVIATION_THRESHOLD_STDDEVS:
                continue

            already_flagged = db.scalar(
                select(DataAnomaly.id).where(
                    DataAnomaly.factory_id == factory.id,
                    DataAnomaly.metric == metric,
                    DataAnomaly.detected_at >= datetime.combine(
                        as_of, datetime.min.time(), tzinfo=timezone.utc
                    ),
                )
            )
            if already_flagged:
                continue

            db.add(
                DataAnomaly(
                    factory_id=factory.id,
                    metric=metric,
                    type="BASELINE_DEVIATION",
                    severity=_severity_for_deviation(stddevs_away),
                    detected_value=round(actual_value, 2),
                    expected_value=round(mean, 2),
                    status="DETECTED",
                    detected_at=datetime.now(timezone.utc),
                )
            )
            created += 1

    db.commit()
    return created
