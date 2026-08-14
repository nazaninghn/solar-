import logging

# Same stub-delivery reasoning as app/auth/email.py (password reset/
# verification) — no real SMTP provider exists in this project yet.
# Kept as a separate module rather than reusing app/auth/email.py:
# that one is Step 24's transactional-auth-email concern (never gated
# by user preference, always sent); this one is preference-gated alert
# email (30.17), a genuinely different trigger and audience.
logger = logging.getLogger(__name__)


def send_notification_email(to_email: str, notification) -> bool:
    """
    30.16's example format: subject line + body built from the
    notification's own title/message, not a separate template per
    alert type — the rules already produce human-readable text.
    """
    logger.info(
        "[STUB EMAIL] SolarFlow Alert to %s: %s — %s",
        to_email,
        notification.title,
        notification.message,
    )
    return True
