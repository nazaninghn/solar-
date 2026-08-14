import json

from sqlalchemy.orm import Session

from app.core.encryption import decrypt_value, encrypt_value
from app.models.device import Device

# 31.22: not exposed via any API endpoint yet — no real protocol
# adapter (Modbus/MQTT/REST) exists to consume a stored config, only
# the inert stub files in app/devices/modbus.py etc. Building a
# credential-management endpoint for a feature nothing uses yet would
# be speculative; this module is the encrypted-storage primitive ready
# for whichever adapter needs it first.


def set_connection_config(db: Session, device: Device, config: dict) -> None:
    device.connection_config_encrypted = encrypt_value(json.dumps(config))
    db.commit()


def get_connection_config(db: Session, device: Device) -> dict | None:
    if device.connection_config_encrypted is None:
        return None

    return json.loads(decrypt_value(device.connection_config_encrypted))
