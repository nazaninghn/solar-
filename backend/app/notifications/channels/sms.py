import logging

# 30.18: no real SMS provider (Twilio etc.) exists — same category as
# Sentry (Step 28) and email (Step 24): stub delivery, ready to swap
# for a real provider behind this one function once an account exists.
# No account is created by this codebase.
logger = logging.getLogger(__name__)


def send_notification_sms(to_phone: str, notification) -> bool:
    """
    Callers are responsible for the CRITICAL-only gate (30.18) — this
    function itself doesn't check severity, so it stays reusable if
    that policy ever needs to change without touching the channel.
    """
    logger.info(
        "[STUB SMS] To %s: SolarFlow Alert: %s",
        to_phone,
        notification.title,
    )
    return True
