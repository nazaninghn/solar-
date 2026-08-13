import json
import logging
import sys

from app.core.config import settings

# Attributes every LogRecord has by default — anything else on a record
# came from a logger.info(..., extra={...}) call and is genuine
# structured context (28.5's factory_id/provider/duration_ms style
# fields), not a formatting internal.
_STANDARD_RECORD_ATTRS = set(
    logging.LogRecord(
        name="", level=0, pathname="", lineno=0, msg="", args=(), exc_info=None
    ).__dict__.keys()
)


class JsonFormatter(logging.Formatter):
    """
    28.5: structured logs — every field a log aggregator (or a human
    grepping raw stdout on Render) can filter on directly, instead of
    parsing free text. Any extra=... fields a caller passes ride along
    automatically; nothing needs to know about this formatter to use it.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "service": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            payload["error"] = self.formatException(record.exc_info)

        for key, value in record.__dict__.items():
            if key not in _STANDARD_RECORD_ATTRS and key not in payload:
                payload[key] = value

        return json.dumps(payload, default=str)


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

    LOG_FORMAT=json switches to structured output (28.5) — defaults to
    plain text locally, since that's more readable in a terminal than
    JSON; production deploys should set LOG_FORMAT=json so a log
    aggregator can parse fields instead of regexing free text.
    """
    level = logging.DEBUG if settings.DEBUG else logging.INFO

    handler = logging.StreamHandler(stream=sys.stdout)

    if settings.LOG_FORMAT == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]

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
