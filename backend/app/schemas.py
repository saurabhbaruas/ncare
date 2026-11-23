"""Request bodies (what the frontend sends) and the user -> JSON helper."""
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator

from app import validators
from app.database import utcnow
from app.security import check_password_policy


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class ResetRequestIn(BaseModel):
    email: EmailStr


class ResetConfirmIn(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, v):
        check_password_policy(v)
        return v


class UserCreateIn(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role_id: int
    location_id: int
    team_id: int

    @field_validator("password")
    @classmethod
    def strong_password(cls, v):
        check_password_policy(v)
        return v

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, v):
        v = v.strip()
        if not v or len(v) > 100:
            raise ValueError("Full name is required (max 100 characters)")
        return v


class StatusIn(BaseModel):
    is_active: bool


class PatientUpdateIn(BaseModel):
    """Every field is optional, the frontend only sends what the manager changed."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None

    @field_validator("first_name")
    @classmethod
    def v_first(cls, v):
        return v if v is None else validators.validate_name(v, "First Name")

    @field_validator("last_name")
    @classmethod
    def v_last(cls, v):
        return v if v is None else validators.validate_name(v, "Last Name")

    @field_validator("dob")
    @classmethod
    def v_dob(cls, v):
        return v if v is None else validators.validate_dob(v)

    @field_validator("gender")
    @classmethod
    def v_gender(cls, v):
        return v if v is None else validators.validate_gender(v)


def user_to_dict(user) -> dict:
    """The user details shown on the dashboards. Never includes the password hash."""
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.name,
        "location": user.location.code,
        "location_name": user.location.name,
        "team": user.team.code,
        "team_name": user.team.name,
        "is_active": user.is_active,
        # only "locked" while the lock time is still in the future
        "is_locked": bool(user.locked_until and user.locked_until > utcnow()),
        "created_at": user.created_at.isoformat(),
        "permissions": sorted(user.role.all_permissions()),
    }
