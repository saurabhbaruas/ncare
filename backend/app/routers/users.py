"""Admin features: user list, create user, enable/disable, login activity. Plus /meta for dropdowns."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user, require_permission
from app.logger import logger
from app.models import AuthLog, Location, Role, Team, User
from app.schemas import StatusIn, UserCreateIn, user_to_dict
from app.security import hash_password

router = APIRouter(tags=["users"])
admin_only = require_permission("users:manage")


@router.get("/meta")
def meta(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    """Dropdown values for the frontend (roles, locations, teams, genders)."""
    return {
        "roles": [{"id": r.id, "name": r.name} for r in db.query(Role).all()],
        "locations": [{"id": l.id, "code": l.code, "name": l.name} for l in db.query(Location).all()],
        "teams": [{"id": t.id, "code": t.code, "name": t.name} for t in db.query(Team).all()],
        "genders": settings.GENDER_OPTIONS,
    }


@router.get("/users")
def list_users(db: Session = Depends(get_db), _admin: User = Depends(admin_only)):
    users = db.query(User).order_by(User.id).all()
    return [user_to_dict(u) for u in users]


@router.post("/users", status_code=201)
def create_user(body: UserCreateIn, db: Session = Depends(get_db), admin: User = Depends(admin_only)):
    # make sure the chosen role/location/team really exist
    if not (db.get(Role, body.role_id) and db.get(Location, body.location_id) and db.get(Team, body.team_id)):
        raise HTTPException(400, "Unknown role, location or team")

    user = User(email=body.email.lower(), full_name=body.full_name,
                password_hash=hash_password(body.password), role_id=body.role_id,
                location_id=body.location_id, team_id=body.team_id)
    try:
        db.add(user)
        db.commit()
    except IntegrityError:
        # the email column is unique
        db.rollback()
        raise HTTPException(409, "A user with this email already exists")

    logger.info(f"USER CREATED {user.email} by {admin.email}")
    return user_to_dict(user)


@router.patch("/users/{user_id}/status")
def set_status(user_id: int, body: StatusIn, db: Session = Depends(get_db),
               admin: User = Depends(admin_only)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    if user.id == admin.id:
        raise HTTPException(400, "You cannot disable your own account")

    user.is_active = body.is_active
    # enabling an account also clears any lockout
    if body.is_active:
        user.failed_attempts = 0
        user.locked_until = None
    db.commit()
    logger.info(f"USER {'ENABLED' if body.is_active else 'DISABLED'} {user.email} by {admin.email}")
    return user_to_dict(user)


@router.get("/activity")
def login_activity(db: Session = Depends(get_db), _admin: User = Depends(admin_only)):
    """Last 20 login attempts, newest first."""
    rows = db.query(AuthLog).order_by(AuthLog.id.desc()).limit(20).all()
    return [{"id": r.id, "email": r.email, "success": r.success, "reason": r.reason,
             "ip_address": r.ip_address, "created_at": r.created_at.isoformat()} for r in rows]
