import logging

from app.core.config import settings

logger = logging.getLogger("app.error_tracking")

# 28.31 (and 27.32): never send these to a third party, full stop.
# Sentry's own "request" event data includes headers/cookies/query
# params by default — this list is what before_send strips before an
# event ever leaves the process.
_SENSITIVE_HEADER_NAMES = {"authorization", "x-device-key", "cookie", "set-cookie"}
_SENSITIVE_BODY_KEYS = {
    "password",
    "jwt",
    "access_token",
    "refresh_token",
    "device_key",
    "api_key",
    "token",
}


def _scrub_event(event: dict, hint: dict) -> dict | None:
    request = event.get("request")

    if request:
        headers = request.get("headers")
        if headers:
            request["headers"] = {
                key: ("[Filtered]" if key.lower() in _SENSITIVE_HEADER_NAMES else value)
                for key, value in headers.items()
            }

        for body_field in ("data", "query_string"):
            body = request.get(body_field)
            if isinstance(body, dict):
                for key in list(body.keys()):
                    if key.lower() in _SENSITIVE_BODY_KEYS:
                        body[key] = "[Filtered]"

    return event


def configure_error_tracking() -> None:
    """
    28.37-28.38: entirely inert unless SENTRY_DSN is set — no Sentry
    account is created by this codebase, and nothing is sent anywhere
    until you supply a real DSN from your own Sentry project.
    """
    if not settings.SENTRY_DSN:
        return

    import sentry_sdk

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.APP_ENV,
        # 28.38: PII (IP addresses, user data) is opt-in in sentry-sdk
        # by default, but stated explicitly here so it stays false even
        # if a future sentry-sdk version changes its own default.
        send_default_pii=False,
        before_send=_scrub_event,
        traces_sample_rate=0.0,
    )

    logger.info("Sentry error tracking initialized (environment=%s)", settings.APP_ENV)
