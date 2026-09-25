from __future__ import annotations

import hashlib
import os


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with a random 16-byte salt.

    Returns the salt (hex) and hash (hex) joined by ':'.
    """
    salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 600_000)
    return f"{salt.hex()}:{pwd_hash.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Verify a password against a hash produced by hash_password()."""
    try:
        salt_hex, hash_hex = stored.split(":")
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
        computed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 600_000)
        return computed == expected
    except (ValueError, TypeError):
        return False