from cryptography.fernet import Fernet

from app.core.config import settings

# 31.22: device connection credentials (Modbus/MQTT host, username,
# password, API key) must never be stored plaintext. Deliberately
# fails loud rather than falling back to a default key the way
# JWT_SECRET's empty-string default does — an unset JWT_SECRET breaks
# auth immediately and visibly, but a *weak default* encryption key
# would silently produce "encrypted-looking" data that isn't actually
# protected, which is a worse failure mode than refusing to run.


def _get_fernet() -> Fernet:
    if not settings.CONNECTION_CONFIG_ENCRYPTION_KEY:
        raise RuntimeError(
            "CONNECTION_CONFIG_ENCRYPTION_KEY is not configured — required before "
            "storing or reading any device connection credentials. Generate one "
            "with: python -c \"from cryptography.fernet import Fernet; "
            'print(Fernet.generate_key().decode())"'
        )

    return Fernet(settings.CONNECTION_CONFIG_ENCRYPTION_KEY.encode())


def encrypt_value(plaintext: str) -> str:
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    return _get_fernet().decrypt(ciphertext.encode()).decode()
