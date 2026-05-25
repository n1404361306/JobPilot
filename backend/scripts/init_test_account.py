import os
import sys

from sqlalchemy import select

# Ensure backend project root is importable when running from scripts/ path.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.role import Role
from app.models.user import User
from app.models.user import UserRole


def run() -> None:
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.username == "admin"))
        if user:
            admin = user
            admin.email = "admin@example.com"
            admin.password_hash = hash_password("Admin@123456")
            admin.is_superuser = True
            admin.is_active = True
            db.add(admin)
            db.commit()
            db.refresh(admin)
            print("admin updated: admin / Admin@123456")
        else:
            admin = User(
                username="admin",
                email="admin@example.com",
                password_hash=hash_password("Admin@123456"),
                is_superuser=True,
                is_active=True,
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            print("admin created: admin / Admin@123456")

        admin_role = db.scalar(select(Role).where(Role.code == "admin"))
        if admin_role:
            relation = db.scalar(
                select(UserRole).where(UserRole.user_id == admin.id, UserRole.role_id == admin_role.id)
            )
            if not relation:
                db.add(UserRole(user_id=admin.id, role_id=admin_role.id))
                db.commit()
                print("admin role relation created")
    finally:
        db.close()


if __name__ == "__main__":
    run()
