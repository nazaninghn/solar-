import logging
import time

from sqlalchemy import event
from sqlalchemy.engine import Engine

from app.core.config import settings

logger = logging.getLogger("app.db")


def register_query_monitoring(engine: Engine) -> None:
    """
    28.14-28.15: logs any query slower than SLOW_QUERY_THRESHOLD_MS.
    Start time is stashed on the DBAPI connection's info dict (the
    standard SQLAlchemy pattern for this) rather than a module-level
    variable, since queries can interleave across connections/threads.
    """

    @event.listens_for(engine, "before_cursor_execute")
    def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault("query_start_time", []).append(time.monotonic())

    @event.listens_for(engine, "after_cursor_execute")
    def _after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        start_times = conn.info.get("query_start_time")

        if not start_times:
            return

        duration_ms = round((time.monotonic() - start_times.pop()) * 1000, 1)

        if duration_ms >= settings.SLOW_QUERY_THRESHOLD_MS:
            logger.warning(
                "SLOW_QUERY duration_ms=%s statement=%s",
                duration_ms,
                statement[:500],
                extra={"duration_ms": duration_ms, "statement": statement[:500]},
            )
