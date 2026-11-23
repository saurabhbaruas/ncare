"""
Database tables.

Roles, locations and teams are rows (not hard-coded enums), so adding a new
one later is just an INSERT - no code change needed.
"""
from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer, LargeBinary,
                        String, Table, Text, UniqueConstraint)
from sqlalchemy.orm import relationship

from app.database import Base, utcnow

# many-to-many link between roles and permissions
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id"), primary_key=True),
)


class Permission(Base):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)  # e.g. "patients:manage"


class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    # a role inherits every permission of its parent (role hierarchy)
    parent_id = Column(ForeignKey("roles.id"), nullable=True)

    parent = relationship("Role", remote_side=[id])
    permissions = relationship("Permission", secondary=role_permissions)

    def all_permissions(self) -> set:
        """Own permissions + everything inherited from parent roles."""
        codes = set()
        role = self
        while role:
            codes |= {p.code for p in role.permissions}
            role = role.parent
        return codes


class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False)  # US, IN, EU, AU
    name = Column(String(100), nullable=False)


class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False)  # AR, EPA, PRI
    name = Column(String(100), nullable=False)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(ForeignKey("roles.id"), nullable=False)
    location_id = Column(ForeignKey("locations.id"), nullable=False)
    team_id = Column(ForeignKey("teams.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    # used for the account lockout feature
    failed_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    role = relationship("Role")
    location = relationship("Location")
    team = relationship("Team")


class AuthLog(Base):
    """One row for every login attempt (audit trail)."""
    __tablename__ = "auth_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("users.id"), nullable=True)  # empty when the email is unknown
    email = Column(String(255), nullable=False)
    success = Column(Boolean, nullable=False)
    reason = Column(String(100), nullable=False)
    ip_address = Column(String(64))
    created_at = Column(DateTime, default=utcnow, nullable=False)


class ResetToken(Base):
    """Password reset tokens. Only the hash is stored, never the token itself."""
    __tablename__ = "reset_tokens"
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(64), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False, nullable=False)


class Patient(Base):
    """
    Patient record. Everything except patient_id is stored encrypted (AES-256-GCM).
    patient_id stays plain text so we can enforce uniqueness and look rows up fast.
    """
    __tablename__ = "patients"
    __table_args__ = (UniqueConstraint("manager_id", "patient_id", name="uq_manager_patient"),)

    id = Column(Integer, primary_key=True)
    patient_id = Column(String(30), nullable=False, index=True)
    manager_id = Column(ForeignKey("users.id"), nullable=False, index=True)  # who uploaded it

    first_name = Column(LargeBinary, nullable=False)
    last_name = Column(LargeBinary, nullable=False)
    dob = Column(LargeBinary, nullable=False)
    gender = Column(LargeBinary, nullable=False)
    key_version = Column(Integer, nullable=False)  # which key encrypted this row

    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class DataAudit(Base):
    """Who touched patient data, and how."""
    __tablename__ = "data_audit"
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("users.id"), nullable=False)
    action = Column(String(30), nullable=False)  # upload / view / edit / delete
    patient_id = Column(String(30), nullable=True)
    detail = Column(Text)
    created_at = Column(DateTime, default=utcnow, nullable=False)
