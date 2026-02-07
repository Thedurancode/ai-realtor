import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class OfferStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    COUNTERED = "countered"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


class FinancingType(str, enum.Enum):
    CASH = "cash"
    CONVENTIONAL = "conventional"
    FHA = "fha"
    VA = "va"
    HARD_MONEY = "hard_money"
    SELLER_FINANCING = "seller_financing"
    OTHER = "other"


class Offer(Base):
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False, index=True)
    buyer_contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)
    parent_offer_id = Column(Integer, ForeignKey("offers.id"), nullable=True)

    # Pricing
    offer_price = Column(Float, nullable=False)
    earnest_money = Column(Float, nullable=True)

    # Terms
    financing_type = Column(Enum(FinancingType), default=FinancingType.CASH)
    closing_days = Column(Integer, nullable=True)
    contingencies = Column(JSON, default=list)
    notes = Column(Text, nullable=True)

    # Status
    status = Column(Enum(OfferStatus), default=OfferStatus.DRAFT)
    is_our_offer = Column(Boolean, default=True)

    # MAO snapshot at time of offer
    mao_low = Column(Float, nullable=True)
    mao_base = Column(Float, nullable=True)
    mao_high = Column(Float, nullable=True)

    # Dates
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    property = relationship("Property", back_populates="offers")
    buyer_contact = relationship("Contact", foreign_keys=[buyer_contact_id])
    parent_offer = relationship("Offer", remote_side=[id], back_populates="counter_offers")
    counter_offers = relationship("Offer", back_populates="parent_offer")
