from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/ai_realtor")

# Fly.io Postgres uses postgres:// but SQLAlchemy requires postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Check if using SQLite
is_sqlite = DATABASE_URL.startswith("sqlite://")

# SQLite-specific optimizations
if is_sqlite:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # Needed for SQLite
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        echo=False  # Set to True for SQL query logging
    )
else:
    # PostgreSQL configuration
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Apply SQLite optimizations on import (if using SQLite)
if is_sqlite:
    try:
        from app.services.sqlite_tuning import sqlite_tuner
        sqlite_tuner.apply_optimizations(engine)
        logger.info("✅ SQLite optimizations applied")
    except ImportError:
        logger.warning("⚠️  SQLite tuning module not available")
    except Exception as e:
        logger.warning("⚠️  Failed to apply SQLite optimizations: %s", e)
