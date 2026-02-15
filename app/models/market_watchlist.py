"""Market Watchlist model — save search criteria and get notified on matches."""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.sql import func

from app.database import Base


class MarketWatchlist(Base):
    __tablename__ = "market_watchlists"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    criteria = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    match_count = Column(Integer, default=0)
    last_matched_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
