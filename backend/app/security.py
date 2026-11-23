"""Password hashing, password rules and JWT helpers."""
import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.config import settings

# argon2id adds a random salt for every hash automatically
hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return hasher.verify(hashed, password)
    except VerifyMismatchError:
        return False


def check_password_policy(password: str) -> None:
    """Raise ValueError with a friendly message if the password is too weak."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password needs at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password needs at least one lowercase letter")
    if not re.search(r"\d", password):
        raise ValueError("Password needs at least one number")
    if not re.search(r"[^A-Za-z0-9]", password):
        raise ValueError("Password needs at least one special character")


def create_access_token(user_id: int) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": expires}, settings.SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    """Raises jwt.PyJWTError when the token is invalid or expired."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])


def new_random_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Fast hash is fine here: reset tokens are long random strings, not passwords."""
    return hashlib.sha256(token.encode()).hexdigest()
