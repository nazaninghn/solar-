import logging

# No SMTP/email provider exists in this project yet (same gap flagged for
# Step 14's SMS/email notifications) — delivery is stubbed via logging.
# Step 27 fixed the reason this used to be print(): nothing configured
# the `logging` module's handlers/levels, so a logger call here went
# nowhere under uvicorn's default setup. Swap this out for a real
# provider (SES, Postmark, etc.) without touching callers once one is
# chosen.
logger = logging.getLogger(__name__)


def send_password_reset_email(email: str, token: str) -> None:
    logger.info(
        "[STUB EMAIL] Password reset requested for %s — reset link: "
        "https://app.solarflow.example/reset-password?token=%s",
        email,
        token,
    )


def send_verification_email(email: str, token: str) -> None:
    logger.info(
        "[STUB EMAIL] Verify email for %s — verification link: "
        "https://app.solarflow.example/verify-email?token=%s",
        email,
        token,
    )
