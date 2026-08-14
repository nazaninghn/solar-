from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_token
from app.database.session import get_db
from app.models.device import Device
from app.models.factory import Factory
from app.modules.security.audit_service import EVENT_SUSPICIOUS_REQUEST, log_security_event


def get_device_from_api_key(
    device_id: int,
    request: Request,
    db: Session = Depends(get_db),
    x_device_key: str | None = Header(default=None),
) -> Device:
    """
    26.15: telemetry ingestion authenticates as the DEVICE, not a user —
    a device has no session, no password, no company login. The key
    proves "this caller is device N", nothing more; it's deliberately
    unable to do anything a normal user endpoint can (list other
    devices, manage users, etc).

    device_id in the path must match the key's own device — otherwise
    a leaked key for device A could be used to inject readings under
    device B's identity within the same factory.
    """
    if not x_device_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Device-Key header",
        )

    device = db.scalar(
        select(Device).where(Device.device_key_hash == hash_token(x_device_key))
    )

    # 26.34: is_active doubles as revocation — a revoked/deactivated
    # device's key stops authenticating immediately, same as it already
    # stops being polled.
    if device is None or not device.is_active:
        log_security_event(
            db,
            event_type=EVENT_SUSPICIOUS_REQUEST,
            severity="INFO",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            description=f"Invalid or revoked device key presented for device_id={device_id}",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked device key",
        )

    if device.id != device_id:
        # 82: a *valid, active* key for one device presented against a
        # different device's path — this is a real cross-device identity
        # mismatch, not a typo/expired-key case, so it's HIGH not INFO.
        factory = db.get(Factory, device.factory_id)
        log_security_event(
            db,
            event_type=EVENT_SUSPICIOUS_REQUEST,
            severity="HIGH",
            organization_id=factory.organization_id if factory else None,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            description=(
                f"Device key for device_id={device.id} presented against "
                f"mismatched path device_id={device_id}"
            ),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device key does not match the requested device",
        )

    return device
