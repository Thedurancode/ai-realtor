"""
Dashboard Model

Saved dashboard configurations for agents.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Dashboard(Base):
    """
    Saved dashboard configuration.

    Agents can create custom dashboards with:
    - Selected widgets (charts, KPIs, tables)
    - Custom layouts
    - Filters and date ranges
    - Sharing settings
    """

    __tablename__ = "dashboards"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)

    # Dashboard metadata
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False)  # One default per agent
    is_public = Column(Boolean, default=False)  # Share with team

    # Dashboard configuration (JSON)
    layout = Column(JSON, nullable=False)  # Widget positions and sizes
    widgets = Column(JSON, nullable=False)  # Widget configurations

    # Filters (saved query parameters)
    filters = Column(JSON, nullable=True)  # Date range, property types, cities, etc.

    # Refresh settings
    auto_refresh = Column(Boolean, default=False)
    refresh_interval_seconds = Column(Integer, default=300)  # 5 minutes default

    # Theme
    theme = Column(String(50), default="default")  # default, dark, light

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    agent = relationship("Agent", back_populates="dashboards")

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "is_default": self.is_default,
            "is_public": self.is_public,
            "layout": self.layout,
            "widgets": self.widgets,
            "filters": self.filters,
            "auto_refresh": self.auto_refresh,
            "refresh_interval_seconds": self.refresh_interval_seconds,
            "theme": self.theme,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
