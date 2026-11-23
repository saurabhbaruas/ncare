"""Login, logout, current user and password reset."""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db, utcnow
from app.deps import get_current_user
from app.limiter import limiter
from app.logger import logger
from app.models import AuthLog, ResetToken, User
from app.schemas import LoginIn, ResetConfirmIn, ResetRequestIn, user_to_dict
from app.security import (create_access_token, hash_password, hash_token,
                          new_random_token, verify_password)

router = APIRouter(prefix="/auth", tags=["auth"])

GENERIC_LOGIN_ERROR = "Invalid email or password"


def record_attempt(db: Session, request: Request, email: str, user, success: bool, reason: str):
    """Saves every login attempt in the audit table and in the info log."""
    ip = request.client.host if request.client else "unknown"
    db.add(AuthLog(user_id=user.id if user else None, email=email,
                   success=success, reason=reason, ip_address=ip))
    db.commit()
    logger.info(f"LOGIN {'OK' if success else 'FAILED'} | {email} | {reason} | ip={ip}")


@router.post("/login")
@limiter.limit(settings.LOGIN_RATE_LIMIT)
def login(request: Request, body: LoginIn, response: Response, db: Session = Depends(get_db)):
    email = body.email.lower()
    user = db.query(User).filter(User.email == email).first()

    # unknown email -> same message as a wrong password, so nobody can guess which emails exist
    if not user:
        record_attempt(db, request, email, None, False, "unknown email")
        raise HTTPException(401, GENERIC_LOGIN_ERROR)

    # still locked from too many failed attempts?
    if user.locked_until and user.locked_until > utcnow():
        minutes = int((user.locked_until - utcnow()).total_seconds() // 60) + 1
        record_attempt(db, request, email, user, False, "account locked")
        raise HTTPException(423, f"Account is locked. Try again in {minutes} minute(s).")

    if not verify_password(body.password, user.password_hash):
        user.failed_attempts += 1
        reason = "wrong password"
        # lock the account after too many wrong passwords
        if user.failed_attempts >= settings.MAX_FAILED_ATTEMPTS:
            user.locked_until = utcnow() + timedelta(minutes=settings.LOCKOUT_MINUTES)
            user.failed_attempts = 0
            reason = "wrong password - account locked"
        db.commit()
        record_attempt(db, request, email, user, False, reason)
        raise HTTPException(401, GENERIC_LOGIN_ERROR)

    # the password is right, but an admin may have disabled the account
    if not user.is_active:
        record_attempt(db, request, email, user, False, "account disabled")
        raise HTTPException(403, "Your account is disabled. Please contact an administrator.")

    # success: clear the failure counters
    user.failed_attempts = 0
    user.locked_until = None
    db.commit()
    record_attempt(db, request, email, user, True, "ok")

    max_age = settings.TOKEN_EXPIRE_MINUTES * 60
    # the JWT lives in an HttpOnly cookie, so JavaScript (and XSS) can never read it
    response.set_cookie("access_token", create_access_token(user.id), max_age=max_age,
                        httponly=True, samesite="lax", secure=settings.COOKIE_SECURE)
    # the CSRF token must be readable by the frontend, so this one is not HttpOnly
    response.set_cookie("csrf_token", new_random_token(), max_age=max_age,
                        httponly=False, samesite="lax", secure=settings.COOKIE_SECURE)
    return user_to_dict(user)


@router.post("/logout")
def logout(response: Response):
    # session cleanup = remove both cookies
    response.delete_cookie("access_token")
    response.delete_cookie("csrf_token")
    return {"message": "Logged out"}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return user_to_dict(user)


@router.post("/password-reset/request")
@limiter.limit(settings.LOGIN_RATE_LIMIT)
def request_reset(request: Request, body: ResetRequestIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower()).first()

    if user and user.is_active:
        token = new_random_token()
        db.add(ResetToken(user_id=user.id, token_hash=hash_token(token),
                          expires_at=utcnow() + timedelta(minutes=settings.RESET_TOKEN_MINUTES)))
        db.commit()
        # No email server in this demo, so the "email" is written to the info log.
        logger.info(f"PASSWORD RESET LINK for {user.email}: "
                    f"{settings.FRONTEND_URL}/reset-password?token={token}")

    # same answer whether the email exists or not
    return {"message": "If that email is registered, a reset link has been sent."}


@router.post("/password-reset/confirm")
def confirm_reset(body: ResetConfirmIn, db: Session = Depends(get_db)):
    record = (db.query(ResetToken)
              .filter(ResetToken.token_hash == hash_token(body.token),
                      ResetToken.used == False,  # noqa: E712
                      ResetToken.expires_at > utcnow())
              .first())
    if not record:
        raise HTTPException(400, "This reset link is invalid or has expired")

    user = db.get(User, record.user_id)
    user.password_hash = hash_password(body.new_password)
    # a reset also unlocks the account
    user.failed_attempts = 0
    user.locked_until = None
    record.used = True
    db.commit()
    logger.info(f"PASSWORD RESET DONE for {user.email}")
    return {"message": "Password updated. You can log in now."}
