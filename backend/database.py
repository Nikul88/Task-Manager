"""
database.py – SQLAlchemy engine & session setup (code-first approach).
Tables are auto-created when the app starts via Base.metadata.create_all().
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
import urllib.parse
DB_NAME = os.getenv("DB_NAME", "taskmanager_db")

encoded_password = urllib.parse.quote_plus(DB_PASSWORD)

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency – yields a DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Called once at startup to create all tables that don't exist yet.
    Import all models before calling this so SQLAlchemy knows about them.
    """
    from models import User, OtpVerification, Project, ProjectMember, Task  # noqa
    Base.metadata.create_all(bind=engine)
