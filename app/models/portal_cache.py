from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func

from app.database import Base


class PortalCache(Base):
    __tablename__ = "portal_cache"

    id = Column(Integer, primary_key=True, index=True)
    url_hash = Column(String(64), nullable=False, unique=True, index=True)
    source_url = Column(String(1000), nullable=False)
    raw_html = Column(Text, nullable=False)
    captured_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
