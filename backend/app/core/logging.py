import logging
import sys

from app.core.config import settings


def configure_logging() -> None:
    """
    27.29-27.31: nothing configured the `logging` module anywhere in
    this project before now — every ad-hoc print() (device_jobs.py,
    retention_jobs.py, the email stub) existed specifically because a
    plain logger.info() call would have gone nowhere under the default
    config. This is that missing configuration, applied once at
    startup, so those call sites can use the real logging module
    instead.

    DEBUG level in development, INFO in staging/production — a
    misconfigured production deploy shouldn't be silently chattier than
    intended, and DEBUG-level logs can include request/query detail
    that's noisy (though never secret; see the "never log" list below)
    at production volume.
    """
    level = logging.DEBUG if settings.DEBUG else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
        force=True,
    )

    # uvicorn/apscheduler already configure their own handlers; align
    # their level with ours instead of leaving them on defaults that
    # might be louder or quieter than the rest of the app.
    logging.getLogger("apscheduler").setLevel(level)


# 27.31: never log — Password, JWT, API Key, Device Key, Refresh Token.
# Nothing in this codebase's logger.* call sites passes any of those
# today (verified: device keys/JWTs are only ever used in comparisons
# or returned in HTTP responses, never interpolated into a log message)
# — kept here as the one place that rule is written down, since it's a
# constraint on every future log call, not a piece of runtime logic.
