import enum

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ClientType(str, enum.Enum):
    BUYER = "buyer"
    SELLER = "seller"
    INVESTOR = "investor"
    TENANT = "tenant"
    LANDLORD = "landlord"


class ClientStatus(str, enum.Enum):
    LEAD = "lead"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    ACTIVE = "active"
    UNDER_CONTRACT = "under_contract"
    CLOSED = "closed"
    INACTIVE = "inactive"


class Client(Base):
    __tablename__ = "clients"
    __table_args__ = (
        Index("ix_clients_agent_id", "agent_id"),
        Index("ix_clients_status", "status"),
        Index("ix_clients_type", "client_type"),
    )

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)

    # Identity
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    company = Column(String, nullable=True)

    client_type = Column(Enum(ClientType), nullable=False)
    status = Column(Enum(ClientStatus), default=ClientStatus.LEAD)
    source = Column(String, nullable=True)  # referral, website, cold call, etc.
    notes = Column(Text, nullable=True)

    # Buyer preferences (nullable for sellers)
    preferred_locations = Column(JSON, default=list)  # list of cities/zips
    budget_min = Column(Float, nullable=True)
    budget_max = Column(Float, nullable=True)
    bedrooms_min = Column(Integer, nullable=True)
    bathrooms_min = Column(Float, nullable=True)
    sqft_min = Column(Integer, nullable=True)
    property_types = Column(JSON, default=list)  # list of property types
    must_haves = Column(JSON, default=list)  # list of required features
    deal_breakers = Column(JSON, default=list)  # list of deal breakers

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    agent = relationship("Agent")
    showings = relationship("Showing", back_populates="client")
    transactions = relationship("Transaction", back_populates="client")
    messages = relationship("Message", back_populates="client")
    commissions = relationship("Commission", back_populates="client")
