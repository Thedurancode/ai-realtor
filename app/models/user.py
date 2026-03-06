"""User model for product purchases."""

from sqlalchemy import Column, String, DateTime, Integer
from datetime import datetime, timezone

from app.database import Base


class User(Base):
    """Basic user model for product ownership."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
