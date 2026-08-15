"""
Email Provider — Resend integration.

Free tier: 100 emails/day, 3000/month.
Sign up at: https://resend.com
Set RESEND_API_KEY in .env

Usage:
    from app.integrations.email_provider import send_email
    await send_email("user@example.com", "Welcome", "<h1>Hello!</h1>")
"""

import logging
import os

import httpx

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "SolarFlow <noreply@solarflow.io>")


async def send_email(to: str, subject: str, html: str) -> bool:
    """
    Send email via Resend API.
    Returns True if sent successfully, False otherwise.
    """
    if not RESEND_API_KEY:
        logger.warning(f"Email not sent (no RESEND_API_KEY): to={to} subject={subject}")
        return False

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
                json={
                    "from": FROM_EMAIL,
                    "to": [to],
                    "subject": subject,
                    "html": html,
                },
            )
            if res.status_code == 200:
                logger.info(f"Email sent: to={to} subject={subject}")
                return True
            else:
                logger.error(f"Email failed: {res.status_code} {res.text}")
                return False
    except Exception as e:
        logger.error(f"Email exception: {e}")
        return False


# Email templates

def welcome_email(name: str) -> tuple[str, str]:
    """Returns (subject, html) for welcome email."""
    return (
        "Welcome to SolarFlow",
        f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #1D1C3B;">Welcome to SolarFlow, {name}!</h1>
            <p>Your AI-powered energy intelligence platform is ready.</p>
            <p>Start by adding your first factory and connecting devices.</p>
            <a href="https://app.solarflow.io/dashboard" 
               style="display: inline-block; padding: 12px 24px; background: #3CB54A; color: white; 
                      text-decoration: none; border-radius: 8px; margin-top: 16px;">
                Go to Dashboard
            </a>
        </div>
        """
    )


def alert_email(title: str, message: str, severity: str) -> tuple[str, str]:
    """Returns (subject, html) for alert notification."""
    color = "#EF4444" if severity == "CRITICAL" else "#FDB94C" if severity == "HIGH" else "#3CB54A"
    return (
        f"SolarFlow Alert: {title}",
        f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: {color}; color: white; padding: 12px 20px; border-radius: 8px 8px 0 0;">
                <strong>{severity}</strong> — {title}
            </div>
            <div style="padding: 20px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
                <p>{message}</p>
                <a href="https://app.solarflow.io/dashboard" style="color: #3CB54A;">View Dashboard →</a>
            </div>
        </div>
        """
    )
