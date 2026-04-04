"""
scripts/init_db.py
──────────────────
Run once to:
  1. Create the MySQL database (if it doesn't exist)
  2. Create all tables
  3. Seed a default admin user

Usage:
    python scripts/init_db.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.db.session import Base, SessionLocal
from app.models import User, FinancialRecord  # noqa – registers models with Base
from app.core.security import hash_password
from app.core.permissions import UserRole


def create_database_if_not_exists():
    # Connect without specifying a DB
    root_url = (
        f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}"
    )
    engine = create_engine(root_url)
    with engine.connect() as conn:
        conn.execute(
            text(
                f"CREATE DATABASE IF NOT EXISTS `{settings.DB_NAME}` "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        )
    print(f"✔  Database '{settings.DB_NAME}' is ready.")
    engine.dispose()


def create_tables():
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    print("✔  All tables created.")
    engine.dispose()


def seed_admin():
    db = SessionLocal()
    try:
        exists = db.query(User).filter(User.email == "admin@example.com").first()
        if exists:
            print("✔  Admin user already exists – skipping seed.")
            return

        admin = User(
            email="admin@example.com",
            full_name="System Admin",
            hashed_password=hash_password("Admin1234!"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        viewer = User(
            email="viewer@example.com",
            full_name="Demo Viewer",
            hashed_password=hash_password("Viewer123!"),
            role=UserRole.VIEWER,
            is_active=True,
        )
        analyst = User(
            email="analyst@example.com",
            full_name="Demo Analyst",
            hashed_password=hash_password("Analyst123!"),
            role=UserRole.ANALYST,
            is_active=True,
        )
        db.add_all([admin, viewer, analyst])
        db.commit()
        print("✔  Seeded users:")
        print("     admin@example.com    / Admin1234!   (admin)")
        print("     analyst@example.com  / Analyst123!  (analyst)")
        print("     viewer@example.com   / Viewer123!   (viewer)")
    finally:
        db.close()


if __name__ == "__main__":
    create_database_if_not_exists()
    create_tables()
    seed_admin()
    print("\n🎉  Database initialisation complete.")
