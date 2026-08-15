"""
Email Service using Resend (free tier: 100 emails/day).
Sign up at https://resend.com → get API key → set RESEND_API_KEY in .env

If no API key is configured, emails are logged to console (dev mode).
"""

import logging
import os

import httpx

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "SolarFlow <noreply@solarflow.io>")


async def send_email(to: str, subject: str, html: str) -> bool:
    """
    Send an email via Resend API.
    Falls back to console logging if no API key is set.
    """
    if not RESEND_API_KEY:
        logger.info(f"[EMAIL DEV MODE] To: {to} | Subject: {subject}")
        logger.info(f"[EMAIL DEV MODE] Body: {html[:200]}...")
        return True

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": FROM_EMAIL,
                    "to": [to],
                    "subject": subject,
                    "html": html,
                },
            )
            if res.status_code == 200:
                logger.info(f"Email sent to {to}: {subject}")
                return True
            else:
                logger.error(f"Email failed: {res.status_code} {res.text}")
                return False
    except Exception as e:
        logger.error(f"Email exception: {e}")
        return False


# --- Pre-built email templates ---

async def send_welcome_email(to: str, name: str) -> bool:
    return await send_email(
        to=to,
        subject="Welcome to SolarFlow ☀️",
        html=f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #1D1C3B;">Welcome to SolarFlow, {name}!</h2>
            <p>Your AI-powered energy intelligence platform is ready.</p>
            <p>Start by adding your first factory and connecting devices.</p>
            <a href="https://solarflow.io/dashboard" style="display: inline-block; padding: 12px 24px; background: #3CB54A; color: white; border-radius: 8px; text-decoration: none; font-weight: bold;">
                Open Dashboard
            </a>
            <p style="color: #666; font-size: 12px; margin-top: 24px;">— The SolarFlow Team</p>
        </div>
        """,
    )


async def send_alert_email(to: str, alert_title: str, alert_message: str) -> bool:
    return await send_email(
        to=to,
        subject=f"⚠️ SolarFlow Alert: {alert_title}",
        html=f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #EF4444;">⚠️ {alert_title}</h2>
            <p>{alert_message}</p>
            <a href="https://solarflow.io/dashboard" style="display: inline-block; padding: 12px 24px; background: #1D1C3B; color: white; border-radius: 8px; text-decoration: none; font-weight: bold;">
                View Dashboard
            </a>
        </div>
        """,
    )


async def send_password_reset_email(to: str, reset_url: str) -> bool:
    return await send_email(
        to=to,
        subject="Reset your SolarFlow password",
        html=f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #1D1C3B;">Password Reset</h2>
            <p>Click below to reset your password. This link expires in 1 hour.</p>
            <a href="{reset_url}" style="display: inline-block; padding: 12px 24px; background: #3CB54A; color: white; border-radius: 8px; text-decoration: none; font-weight: bold;">
                Reset Password
            </a>
            <p style="color: #666; font-size: 12px; margin-top: 24px;">If you didn't request this, ignore this email.</p>
        </div>
        """,
    )
