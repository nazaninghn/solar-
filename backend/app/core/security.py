import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core.config import settings


password_hash = PasswordHash.recommended()


def hash_token(token: str) -> str:
    """
    24.14: refresh/reset tokens are high-entropy random-looking JWTs
    (not human-chosen passwords), so a fast cryptographic hash is the
    right tool here — unlike hash_password's deliberately slow Argon2,
    which exists specifically to resist brute-forcing a low-entropy
    human password. Storing only the hash still means a stolen DB row
    can't be replayed as a usable token.
    """
    return hashlib.sha256(token.encode()).hexdigest()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(
    password: str,
    hashed_password: str,
) -> bool:
    return password_hash.verify(
        password,
        hashed_password,
    )


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": expire,
        # 82: without a per-token nonce, two tokens minted for the same
        # user with the same expiry second (e.g. back-to-back refresh
        # calls) are byte-identical JWTs — jwt.encode is deterministic
        # for a given payload+secret. That collision silently defeated
        # refresh-token-reuse detection: rotating a token minted the
        # exact same string as the one just revoked, so "reusing the
        # revoked token" and "using the valid new one" were the same
        # request. jti guarantees distinct tokens even when minted in
        # the same second.
        "jti": secrets.token_hex(16),
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
        "jti": secrets.token_hex(16),
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
    )
