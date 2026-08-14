"""
STEP 78: real Postgres table-size measurement — the actual storage
footprint, not a policy document guessing at it. Used by both capacity
snapshots (app/jobs/finops_jobs.py) and the cost-attribution model
(app/modules/finops/service.py).
"""

from sqlalchemy import text
from sqlalchemy.orm import Session

# The tables identified as the fastest-growing during Step 78's
# pre-build inventory, ranked by write frequency. Not every table in
# the system — just the ones actually worth watching for storage cost.
HIGH_VOLUME_TABLES = (
    "device_energy_readings",
    "raw_telemetry",
    "system_metric_snapshots",
    "telemetry_5m",
    "telemetry_hourly",
    "energy_readings",
)


def get_table_sizes_bytes(db: Session) -> dict[str, int]:
    """One real pg_total_relation_size() call per table (includes
    indexes and TOAST, not just row data — the number that actually
    matches what a hosting provider bills for). Tables that don't exist
    in this deployment yet are skipped rather than raising."""
    sizes: dict[str, int] = {}

    existing = set(
        db.scalars(
            text(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public' "
                "AND tablename = ANY(:names)"
            ).bindparams(names=list(HIGH_VOLUME_TABLES))
        ).all()
    )

    for table in HIGH_VOLUME_TABLES:
        if table not in existing:
            continue
        size = db.scalar(
            text("SELECT pg_total_relation_size(:name)").bindparams(name=table)
        )
        sizes[table] = int(size or 0)

    return sizes


def get_total_database_size_bytes(db: Session) -> int:
    return int(db.scalar(text("SELECT pg_database_size(current_database())")) or 0)
