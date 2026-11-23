"""Dependencies that protect the endpoints: who is calling, and are they allowed?"""
import secrets

import jwt
from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.logger import logger
from app.models import User
from app.security import decode_access_token

SAFE_METHODS = ("GET", "HEAD", "OPTIONS")

# Declaring the header like this also adds an "Authorize" button to the Swagger page
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(api_key_header)):
    """First gate for every /api endpoint: the caller must know the API key."""
    # compare_digest takes the same time for any input, so the key can't be guessed by timing
    if not api_key or not secrets.compare_digest(api_key, settings.API_KEY):
        logger.warning("Request rejected: missing or wrong API key")
        # 403 (not 401) so the frontend doesn't mistake it for an expired login
        raise HTTPException(403, "Invalid or missing API key")


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Reads the login cookie and returns the user, or answers 401/403."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(401, "Please log in to continue")

    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError:
        raise HTTPException(401, "Your session has expired, please log in again")

    user = db.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(401, "Your account is not available")

    # CSRF protection: anything that changes data must send the token
    # from the csrf_token cookie back in a header (a malicious site cannot read our cookie).
    if request.method not in SAFE_METHODS:
        cookie = request.cookies.get("csrf_token", "")
        header = request.headers.get("X-CSRF-Token", "")
        if not cookie or not secrets.compare_digest(cookie, header):
            raise HTTPException(403, "Security check failed, please refresh the page")

    return user


def require_permission(code: str):
    """Use as Depends(require_permission('users:manage')) on an endpoint."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if code not in user.role.all_permissions():
            raise HTTPException(403, "You do not have access to this feature")
        return user

    return checker
