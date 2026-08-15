"""
STEP 47.8-47.9: Brute Force Protection & Account Lockout.
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.modules.security.models import AccountLockout, SecurityEvent

logger = logging.getLogger(__name__)

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30


def record_failed_login(db: Session, user_id: int, ip_address: str | None = None) -> bool:
    """Record a failed login attempt. Returns True if account is now locked."""
    now = datetime.now(timezone.utc)

    lockout = db.query(AccountLockout).filter(AccountLockout.user_id == user_id).first()
    if not lockout:
        lockout = AccountLockout(user_id=user_id, failed_attempts=0, created_at=now)
        db.add(lockout)

    lockout.failed_attempts += 1
    lockout.last_failed_at = now
    lockout.updated_at = now

    # Lock account after max attempts
    if lockout.failed_attempts >= MAX_FAILED_ATTEMPTS:
        lockout.locked_until = now + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        lockout.locked_reason = f"Too many failed attempts ({lockout.failed_attempts})"

        # Security event
        db.add(SecurityEvent(
            user_id=user_id,
            event_type="ACCOUNT_LOCKED",
            severity="HIGH",
            ip_address=ip_address,
            description=f"Account locked after {lockout.failed_attempts} failed attempts",
            created_at=now,
        ))
        db.commit()
        logger.warning(f"Account locked: user_id={user_id} attempts={lockout.failed_attempts}")
        return True

    db.commit()
    return False


def is_account_locked(db: Session, user_id: int) -> bool:
    """Check if account is currently locked."""
    lockout = db.query(AccountLockout).filter(AccountLockout.user_id == user_id).first()
    if not lockout or not lockout.locked_until:
        return False

    now = datetime.now(timezone.utc)
    if lockout.locked_until > now:
        return True

    # Lockout expired — reset
    lockout.failed_attempts = 0
    lockout.locked_until = None
    lockout.locked_reason = None
    lockout.updated_at = now
    db.commit()
    return False


def record_successful_login(db: Session, user_id: int) -> None:
    """Reset lockout on successful login.

    86: no longer logs its own LOGIN_SUCCESS SecurityEvent - Step 82
    already made app/modules/auth/router.py's login() the single call
    site for that (with the request's ip_address/user_agent, which
    this function never had access to). Logging it here too would
    double-count every successful login in SecurityEvent and in the
    Step 79 correlation job that reads it.
    """
    lockout = db.query(AccountLockout).filter(AccountLockout.user_id == user_id).first()
    if lockout and lockout.failed_attempts > 0:
        lockout.failed_attempts = 0
        lockout.locked_until = None
        lockout.locked_reason = None
        lockout.updated_at = datetime.now(timezone.utc)
        db.commit()
