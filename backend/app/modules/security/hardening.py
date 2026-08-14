"""
STEP 53: Security Hardening utilities.

Input sanitization, IDOR protection, Mass Assignment guard,
Request size validation, SSRF protection.
"""

import ipaddress
import logging
import re
from urllib.parse import urlparse

from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)

# 53.44: Max request body size (10MB default)
MAX_BODY_SIZE_BYTES = 10 * 1024 * 1024

# 53.69: SSRF protection — blocked IP ranges
BLOCKED_IP_RANGES = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local / metadata
    ipaddress.ip_network("0.0.0.0/8"),
]

# 53.20: Path traversal patterns
PATH_TRAVERSAL_PATTERNS = [
    "..",
    "..\\",
    "../",
    "%2e%2e",
    "%252e%252e",
]

# 53.13: Fields that should never be mass-assignable
PROTECTED_FIELDS = {
    "id",
    "role",
    "is_active",
    "is_admin",
    "is_platform_admin",
    "organization_id",
    "created_at",
    "password_hash",
    "is_verified",
    "is_superuser",
}


def validate_no_path_traversal(path: str) -> bool:
    """53.20: Check for path traversal attempts."""
    for pattern in PATH_TRAVERSAL_PATTERNS:
        if pattern in path.lower():
            logger.warning(f"Path traversal attempt detected: {path}")
            return False
    return True


def validate_url_not_ssrf(url: str) -> bool:
    """53.69: Validate URL is not targeting internal/private networks."""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False

        # Block common internal hostnames
        blocked_hosts = {"localhost", "127.0.0.1", "0.0.0.0", "metadata", "metadata.google.internal"}
        if hostname.lower() in blocked_hosts:
            return False

        # Check IP ranges
        try:
            ip = ipaddress.ip_address(hostname)
            for network in BLOCKED_IP_RANGES:
                if ip in network:
                    logger.warning(f"SSRF blocked: {url} resolves to private IP {ip}")
                    return False
        except ValueError:
            pass  # Not an IP — hostname is fine

        return True
    except Exception:
        return False


def strip_protected_fields(data: dict) -> dict:
    """53.13: Remove protected fields from user input."""
    return {k: v for k, v in data.items() if k not in PROTECTED_FIELDS}


def validate_filename(filename: str) -> str:
    """53.22: Sanitize uploaded filename."""
    # Remove path separators
    filename = filename.replace("/", "").replace("\\", "").replace("..", "")
    # Only allow safe characters
    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    return filename


def validate_file_extension(filename: str, allowed_extensions: set[str]) -> bool:
    """53.21: Validate file extension against allowlist."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in allowed_extensions


# 53.37: Prevent account enumeration
GENERIC_AUTH_ERROR = "Invalid credentials or account does not exist."
GENERIC_RESET_MESSAGE = "If an account exists with that email, a reset link has been sent."
