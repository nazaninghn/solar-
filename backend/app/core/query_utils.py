"""
STEP 86: `func.date(some_timestamptz_column)` truncates using the
database session's own timezone setting, not UTC — confirmed on this
deployment's Postgres, whose session timezone is `America/Los_Angeles`,
while every `created_at`/`timestamp` column in this app is written via
`datetime.now(timezone.utc)`. For roughly 7-8 hours of every UTC day
(whenever it's already tomorrow in UTC but still today in the session's
timezone), `func.date()` and Python's own `datetime.now(timezone.utc)
.date()` disagree — a real bug this step's own regression suite caught
(a flaky BI funnel test that only failed near the UTC/Pacific date
boundary). `utc_date()` forces the conversion explicitly so day-grouped
queries match what "today" means everywhere else in this codebase.
"""

from sqlalchemy import ColumnElement, func


def utc_date(column: ColumnElement) -> ColumnElement:
    return func.date(func.timezone("UTC", column))
