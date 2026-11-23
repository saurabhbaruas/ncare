"""
Field-level encryption for patient data (AES-256-GCM).

- Every value gets its own random nonce, so equal names never look equal in the DB.
- The field name + patient id are bound in as "associated data", so a ciphertext
  copied from one row/column to another fails to decrypt.
- Each row remembers the key version it was encrypted with, which makes key
  rotation possible (see rotate_keys.py).
"""
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import settings

# the columns that get encrypted
FIELDS = ["first_name", "last_name", "dob", "gender"]

# build the AES objects once, they can be reused for every call
_ciphers = {version: AESGCM(key) for version, key in settings.ENCRYPTION_KEYS.items()}


def _encrypt(text: str, version: int, aad: str) -> bytes:
    # 12 random bytes in front of the ciphertext so we can read them back later
    nonce = os.urandom(12)
    return nonce + _ciphers[version].encrypt(nonce, text.encode(), aad.encode())


def _decrypt(blob: bytes, version: int, aad: str) -> str:
    nonce, data = blob[:12], blob[12:]
    try:
        return _ciphers[version].decrypt(nonce, data, aad.encode()).decode()
    except InvalidTag:
        # wrong key or tampered data - never return garbage silently
        raise ValueError("Could not decrypt patient data (wrong key or data was modified)")


def encrypt_patient(patient_id: str, data: dict) -> dict:
    """Takes plain values, returns the encrypted columns + the key version used."""
    version = settings.ACTIVE_KEY_VERSION
    result = {f: _encrypt(data[f], version, f"{f}:{patient_id}") for f in FIELDS}
    result["key_version"] = version
    return result


def decrypt_patient(row) -> dict:
    """Takes a Patient row, returns the plain values."""
    return {f: _decrypt(getattr(row, f), row.key_version, f"{f}:{row.patient_id}") for f in FIELDS}
