import re
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.email import send_password_reset_email, send_verification_email
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.email_verification_token import EmailVerificationToken
from app.models.organization import Organization
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.modules.security.audit_service import EVENT_TOKEN_REUSE, log_security_event


def register_user(
    db: Session,
    email: str,
    password: str,
    full_name: str,
    organization_name: str,
):
    existing_user = db.scalar(
        select(User).where(User.email == email)
    )

    if existing_user:
        raise ValueError("Email already registered")

    organization = Organization(
        name=organization_name,
    )

    db.add(organization)
    db.flush()

    # The f2ca379d4467 migration backfilled slugs for pre-Step-24
    # organizations with this same "slugified-name + id" shape — new
    # registrations need the same so every company has one, not just
    # ones that predate this column.
    organization.slug = (
        re.sub(r"[^a-zA-Z0-9]+", "-", organization_name).strip("-").lower()
        + f"-{organization.id}"
    )

    user = User(
        organization_id=organization.id,
        email=email,
        # Note: our Step 4 User model names this column `hashed_password`,
        # not `password_hash` — same field, adapted to match the existing
        # migration rather than adding a new one to rename it.
        hashed_password=hash_password(password),
        full_name=full_name,
        # Self-registration creates a new company — its first user is
        # that company's admin (24.2), not a platform-wide SUPER_ADMIN.
        role="COMPANY_ADMIN",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    _issue_verification_token(db, user)

    return user


def _issue_verification_token(db: Session, user: User) -> None:
    raw_token = secrets.token_urlsafe(32)

    db.add(
        EmailVerificationToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(timezone.utc)
            + timedelta(hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS),
            created_at=datetime.now(timezone.utc),
        )
    )
    db.commit()

    send_verification_email(user.email, raw_token)


def verify_email(db: Session, token: str) -> None:
    stored = db.scalar(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == hash_token(token)
        )
    )

    if (
        stored is None
        or stored.used_at is not None
        or stored.expires_at < datetime.now(timezone.utc)
    ):
        raise ValueError("Invalid or expired verification token")

    user = db.get(User, stored.user_id)

    if user is None:
        raise ValueError("Invalid or expired verification token")

    user.is_verified = True
    stored.used_at = datetime.now(timezone.utc)
    db.commit()


def resend_verification_email(db: Session, email: str) -> None:
    user = db.scalar(select(User).where(User.email == email))

    # Same "always behave the same either way" principle as
    # request_password_reset — don't let this endpoint confirm whether
    # an email is registered.
    if user is None or user.is_verified:
        return

    _issue_verification_token(db, user)


def authenticate_user(
    db: Session,
    email: str,
    password: str,
):
    user = db.scalar(
        select(User).where(User.email == email)
    )

    if not user:
        return None

    if not user.is_active:
        return None

    if not verify_password(
        password,
        user.hashed_password,
    ):
        return None

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    return user


def create_tokens(db: Session, user: User) -> dict:
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    # 24.14: persisted so it can actually be revoked later — a bare JWT
    # being merely "not expired yet" gives the server no way to reject
    # it before then.
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            created_at=datetime.now(timezone.utc),
        )
    )
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


def refresh_access_token(
    db: Session,
    refresh_token_value: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> dict:
    """24.13, with rotation (24.35): the old refresh token is revoked and
    a brand new access+refresh pair is issued, rather than reusing the
    same refresh token indefinitely."""
    try:
        payload = decode_token(refresh_token_value)
    except jwt.InvalidTokenError as error:
        raise ValueError("Invalid or expired refresh token") from error

    if payload.get("type") != "refresh":
        raise ValueError("Invalid token type")

    stored = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_token(refresh_token_value)
        )
    )

    if stored is not None and stored.revoked_at is not None:
        # 82: a refresh token is only ever revoked by this function's own
        # rotation, or by logout. Someone presenting it again means either
        # the legitimate client retried a stale token, or it was stolen
        # after being rotated out — worth a real security event either way,
        # since it's the one case a bare "expired" can't explain.
        log_security_event(
            db,
            event_type=EVENT_TOKEN_REUSE,
            severity="HIGH",
            user_id=stored.user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            description="Reuse of an already-rotated refresh token",
        )
        raise ValueError("Refresh token has been revoked or is no longer valid")

    if stored is None or stored.expires_at < datetime.now(timezone.utc):
        raise ValueError("Refresh token has been revoked or is no longer valid")

    user_id = payload.get("sub")
    user = db.get(User, int(user_id)) if user_id else None

    if user is None or not user.is_active:
        raise ValueError("User not found or inactive")

    stored.revoked_at = datetime.now(timezone.utc)
    db.commit()

    return create_tokens(db, user)


def logout(db: Session, refresh_token_value: str) -> None:
    stored = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_token(refresh_token_value)
        )
    )

    if stored and stored.revoked_at is None:
        stored.revoked_at = datetime.now(timezone.utc)
        db.commit()


def request_password_reset(db: Session, email: str) -> None:
    """Always returns without error, whether or not the email exists —
    a differing response (404 vs 200) would let a caller enumerate
    registered emails via this endpoint."""
    user = db.scalar(select(User).where(User.email == email))

    if user is None or not user.is_active:
        return

    raw_token = secrets.token_urlsafe(32)

    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(timezone.utc)
            + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES),
            created_at=datetime.now(timezone.utc),
        )
    )
    db.commit()

    send_password_reset_email(user.email, raw_token)


def reset_password(db: Session, token: str, new_password: str) -> None:
    stored = db.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == hash_token(token)
        )
    )

    if (
        stored is None
        or stored.used_at is not None
        or stored.expires_at < datetime.now(timezone.utc)
    ):
        raise ValueError("Invalid or expired reset token")

    user = db.get(User, stored.user_id)

    if user is None:
        raise ValueError("Invalid or expired reset token")

    user.hashed_password = hash_password(new_password)
    stored.used_at = datetime.now(timezone.utc)

    # A password reset is a strong signal of possible compromise —
    # revoke every existing session rather than leaving old refresh
    # tokens (e.g. on a stolen device) valid after the password changes.
    active_refresh_tokens = db.scalars(
        select(RefreshToken).where(
            RefreshToken.user_id == user.id,
            RefreshToken.revoked_at.is_(None),
        )
    )
    for token_row in active_refresh_tokens:
        token_row.revoked_at = datetime.now(timezone.utc)

    db.commit()
