import enum

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ListingStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PENDING = "pending"
    SOLD = "sold"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


class Listing(Base):
    __tablename__ = "listings"
    __table_args__ = (
        Index("ix_listings_property_id", "property_id"),
        Index("ix_listings_status", "status"),
        Index("ix_listings_agent_id", "agent_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)

    status = Column(Enum(ListingStatus), default=ListingStatus.DRAFT)
    list_price = Column(Float, nullable=False)
    original_price = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    mls_number = Column(String, nullable=True)

    published_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    sold_at = Column(DateTime(timezone=True), nullable=True)
    sold_price = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    property = relationship("Property")
    agent = relationship("Agent")
    price_history = relationship("ListingPriceChange", back_populates="listing", order_by="ListingPriceChange.changed_at.desc()")


class ListingPriceChange(Base):
    __tablename__ = "listing_price_changes"
    __table_args__ = (
        Index("ix_listing_price_changes_listing_id", "listing_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)

    old_price = Column(Float, nullable=False)
    new_price = Column(Float, nullable=False)
    reason = Column(String, nullable=True)
    changed_at = Column(DateTime(timezone=True), server_default=func.now())

    listing = relationship("Listing", back_populates="price_history")
