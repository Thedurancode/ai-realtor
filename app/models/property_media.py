import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class MediaType(str, enum.Enum):
    PHOTO = "photo"
    VIDEO = "video"
    FLOOR_PLAN = "floor_plan"
    VIRTUAL_TOUR = "virtual_tour"
    DOCUMENT = "document"


class PropertyMedia(Base):
    __tablename__ = "property_media"
    __table_args__ = (
        Index("ix_property_media_property_id", "property_id"),
        Index("ix_property_media_type", "media_type"),
    )

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)

    media_type = Column(Enum(MediaType), default=MediaType.PHOTO)
    url = Column(String, nullable=False)
    filename = Column(String, nullable=True)
    caption = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0)
    is_primary = Column(Integer, default=0)  # 1 = primary/cover photo

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    property = relationship("Property")
