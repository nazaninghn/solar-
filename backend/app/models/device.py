from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    factory_id: Mapped[int] = mapped_column(
        ForeignKey(
            "factories.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    device_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    manufacturer: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    serial_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    connection_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # 26.15-26.16: never store the raw key, same principle as passwords
    # and refresh tokens — hashed with hash_token (sha256), not
    # hash_password, since this is a high-entropy generated credential
    # rather than a human-chosen one. Nullable because polling-only
    # devices (SIMULATOR today, eventually MODBUS/MQTT) never receive
    # inbound telemetry pushes and so never need a key.
    device_key_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # 26.34's "Device Revocation" is deliberately not a separate
    # revoked/revoked_at pair — is_active already means "stop trusting
    # this device" everywhere else in the codebase (excluded from
    # polling, from telemetry auth, from device lists). A second flag
    # for the same concept would just be two ways to say the same thing.
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Folded in from 16.13-16.14 rather than a follow-up migration,
    # since the model is being built fresh in this same step.
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="UNKNOWN",
    )

    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
