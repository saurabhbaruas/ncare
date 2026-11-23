"""
All the settings of the app live here.
Values come from the .env file (or real environment variables), so nothing
secret is hard-coded in the source.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Look for .env in the project root first, then inside backend/.
# Variables that are already set (e.g. by docker compose) are never overridden.
load_dotenv(BASE_DIR.parent / ".env")
load_dotenv(BASE_DIR / ".env")


def _required(name: str) -> str:
    """Read a mandatory variable, stop early with a clear message if it is missing."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing {name}. Copy .env.example to .env and fill it in.")
    return value


def _load_keys(raw: str) -> dict:
    """Turn '1:base64key,2:base64key' into {1: b'...', 2: b'...'}."""
    import base64

    keys = {}
    for item in raw.split(","):
        version, key = item.strip().split(":", 1)
        decoded = base64.b64decode(key)
        if len(decoded) != 32:
            raise RuntimeError("Every encryption key must be exactly 32 bytes (AES-256).")
        keys[int(version)] = decoded
    return keys


class Settings:
    APP_NAME = "Ncare"

    # ---- database ----
    # SQLite works out of the box; docker compose switches this to PostgreSQL.
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'ncare.db'}")

    # ---- API key: every client must send it in the X-API-Key header ----
    API_KEY = _required("API_KEY")

    # ---- login / session ----
    SECRET_KEY = _required("SECRET_KEY")
    TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "60"))
    COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    MAX_FAILED_ATTEMPTS = int(os.getenv("MAX_FAILED_ATTEMPTS", "5"))
    LOCKOUT_MINUTES = int(os.getenv("LOCKOUT_MINUTES", "15"))
    RESET_TOKEN_MINUTES = int(os.getenv("RESET_TOKEN_MINUTES", "30"))
    LOGIN_RATE_LIMIT = os.getenv("LOGIN_RATE_LIMIT", "10/minute")
    DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "Demo@1234")

    # ---- encryption ----
    ENCRYPTION_KEYS = _load_keys(_required("ENCRYPTION_KEYS"))
    ACTIVE_KEY_VERSION = int(os.getenv("ACTIVE_KEY_VERSION", "1"))

    # ---- patient upload rules ----
    MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))
    MAX_UPLOAD_ROWS = int(os.getenv("MAX_UPLOAD_ROWS", "10000"))
    GENDER_OPTIONS = ["Male", "Female", "Other", "Prefer not to say"]

    # ---- misc ----
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
    CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", FRONTEND_URL).split(",")]
    LOG_DIR = Path(os.getenv("LOG_DIR", BASE_DIR / "logs"))


settings = Settings()

# Fail at startup (not at the first upload) if the active key is not configured.
if settings.ACTIVE_KEY_VERSION not in settings.ENCRYPTION_KEYS:
    raise RuntimeError("ACTIVE_KEY_VERSION is not present in ENCRYPTION_KEYS.")
