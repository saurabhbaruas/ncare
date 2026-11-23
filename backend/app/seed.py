"""
Demo data: roles, permissions, locations, teams and a user for every combination.
Runs automatically on the first start (only if the database is empty).
Can also be run by hand:  python -m app.seed
"""
from sqlalchemy.orm import Session

from app.config import settings
from app.logger import logger
from app.models import Location, Permission, Role, Team, User
from app.security import hash_password

LOCATIONS = {"US": "United States", "IN": "India", "EU": "Europe", "AU": "Australia"}
TEAMS = {"AR": "Accounts Receivable", "EPA": "Environmental Protection Agency", "PRI": "Priority Team"}


def seed(db: Session):
    # already seeded? then do nothing
    if db.query(Role).count():
        return

    # permissions -> roles. Manager and Admin both inherit from User (the parent role).
    perms = {code: Permission(code=code) for code in ("profile:view", "users:manage", "patients:manage")}
    user_role = Role(name="User", permissions=[perms["profile:view"]])
    manager_role = Role(name="Manager", parent=user_role, permissions=[perms["patients:manage"]])
    admin_role = Role(name="Admin", parent=user_role, permissions=[perms["users:manage"]])

    locations = {code: Location(code=code, name=name) for code, name in LOCATIONS.items()}
    teams = {code: Team(code=code, name=name) for code, name in TEAMS.items()}
    db.add_all([user_role, manager_role, admin_role, *locations.values(), *teams.values()])
    db.flush()

    # hash once and reuse - every demo account shares the same demo password
    password_hash = hash_password(settings.DEMO_PASSWORD)
    users = [User(email="admin@ncare.com", full_name="Ada Admin", password_hash=password_hash,
                  role_id=admin_role.id, location_id=locations["US"].id, team_id=teams["PRI"].id)]

    # one manager and one user for each location + team combination
    for loc_code, loc in locations.items():
        for team_code, team in teams.items():
            for role in (manager_role, user_role):
                users.append(User(
                    email=f"{role.name.lower()}.{loc_code.lower()}.{team_code.lower()}@ncare.com",
                    full_name=f"{loc_code} {team_code} {role.name}",
                    password_hash=password_hash,
                    role_id=role.id, location_id=loc.id, team_id=team.id,
                ))

    db.add_all(users)
    db.commit()
    logger.info(f"Seeded demo data: {len(users)} users")


if __name__ == "__main__":
    from app.database import Base, SessionLocal, engine

    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        seed(session)
