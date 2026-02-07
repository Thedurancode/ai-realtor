from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class PropertyStatus(str, enum.Enum):
    AVAILABLE = "available"
    PENDING = "pending"
    SOLD = "sold"
    RENTED = "rented"
    OFF_MARKET = "off_market"


class PropertyType(str, enum.Enum):
    HOUSE = "house"
    APARTMENT = "apartment"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    LAND = "land"
    COMMERCIAL = "commercial"


class DealType(str, enum.Enum):
    TRADITIONAL = "traditional"
    SHORT_SALE = "short_sale"
    REO = "reo"
    FSBO = "fsbo"
    NEW_CONSTRUCTION = "new_construction"
    WHOLESALE = "wholesale"
    RENTAL = "rental"
    COMMERCIAL = "commercial"


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    zip_code = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    bedrooms = Column(Integer, nullable=True)
    bathrooms = Column(Float, nullable=True)
    square_feet = Column(Integer, nullable=True)
    lot_size = Column(Float, nullable=True)
    year_built = Column(Integer, nullable=True)
    property_type = Column(Enum(PropertyType), default=PropertyType.HOUSE)
    status = Column(Enum(PropertyStatus), default=PropertyStatus.AVAILABLE)
    deal_type = Column(Enum(DealType), nullable=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    agent = relationship("Agent", back_populates="properties")
    skip_traces = relationship("SkipTrace", back_populates="property")
    contacts = relationship("Contact", back_populates="property")
    todos = relationship("Todo", back_populates="property")
    contracts = relationship("Contract", back_populates="property")
    zillow_enrichment = relationship("ZillowEnrichment", back_populates="property", uselist=False)
    recap = relationship("PropertyRecap", back_populates="property", uselist=False)
    offers = relationship("Offer", back_populates="property")
