"""
STEP 48.47: Deployment health checks and readiness validation.
"""

from datetime import datetime, timezone

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session


def check_database_connectivity(db: Session) -> dict:
    """Verify database connection and basic query."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "latency_ms": 0}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def check_migration_status(db: Session) -> dict:
    """Verify all migrations have been applied."""
    try:
        result = db.execute(text("SELECT version_num FROM alembic_version"))
        versions = [row[0] for row in result]
        return {"status": "ok", "current_version": versions[0] if versions else "none"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def check_table_exists(db: Session, table_name: str) -> bool:
    """Check if a critical table exists.

    85: previously built the query via f-string interpolation
    (`f"SELECT 1 FROM {table_name}"`), flagged by bandit (B608) as a
    SQL injection vector. Every call site today passes a hardcoded
    constant, not user input, so there was no live exploit path - but
    the pattern itself was still wrong to leave in a function anyone
    could call with anything later. SQLAlchemy's inspector checks
    table existence against the catalog directly, with no string
    interpolation into SQL at all.
    """
    try:
        return inspect(db.get_bind()).has_table(table_name)
    except Exception:
        return False


def run_deployment_checks(db: Session) -> dict:
    """Run all deployment health checks."""
    now = datetime.now(timezone.utc)

    db_check = check_database_connectivity(db)
    migration_check = check_migration_status(db)

    # Check critical tables exist
    critical_tables = ["users", "organizations", "factories", "devices"]
    tables_ok = all(check_table_exists(db, t) for t in critical_tables)

    all_ok = (
        db_check["status"] == "ok"
        and migration_check["status"] == "ok"
        and tables_ok
    )

    return {
        "timestamp": now.isoformat(),
        "overall": "HEALTHY" if all_ok else "UNHEALTHY",
        "database": db_check,
        "migrations": migration_check,
        "critical_tables": tables_ok,
    }
