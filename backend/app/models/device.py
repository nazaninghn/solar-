from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
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

    # 31.17: "Error Count" / "Last Error" — resets to 0/None on the next
    # successful poll (app/jobs/device_jobs.py), so this tracks
    # *consecutive* failures, not a lifetime total. That's the shape
    # calculate_device_health_score (app/devices/health.py) actually
    # needs — a device that failed 50 times last month and has been
    # fine since shouldn't score worse than one that just started
    # failing.
    consecutive_error_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    last_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 31.22: Fernet ciphertext (app/core/encryption.py), never plaintext
    # — holds a JSON-serialized dict of whatever a real protocol adapter
    # needs (Modbus host/port/unit id, MQTT broker/username/password,
    # a REST API key, etc.). Nullable because SIMULATOR devices (the
    # only kind that actually work today — see app/devices/modbus.py/
    # mqtt.py/api.py's inert-stub docstrings) have no credentials to
    # store. Read/write through app.modules.devices.connection_config,
    # never accessed directly.
    connection_config_encrypted: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
