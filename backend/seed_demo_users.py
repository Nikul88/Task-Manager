"""
Create or update default testing users.

Usage:
  python seed_demo_users.py
"""

from auth import hash_password
from database import SessionLocal
import models


def upsert_user(db, name: str, email: str, password: str, role: models.UserRole):
    user = db.query(models.User).filter(models.User.email == email).first()
    if user:
        user.name = name
        user.password_hash = hash_password(password)
        user.role = role
        user.is_verified = True
        return "updated"

    db.add(
        models.User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role=role,
            is_verified=True,
        )
    )
    return "created"


def main():
    db = SessionLocal()
    try:
        admin_action = upsert_user(
            db=db,
            name="Admin User",
            email="admin@taskflow.com",
            password="Admin@12345",
            role=models.UserRole.admin,
        )
        demo_action = upsert_user(
            db=db,
            name="Demo User",
            email="demo@taskflow.com",
            password="Demo@12345",
            role=models.UserRole.member,
        )
        db.commit()
        print(f"admin@taskflow.com: {admin_action}")
        print(f"demo@taskflow.com: {demo_action}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
