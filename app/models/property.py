from sqlalchemy import Column, Index, Integer, String, Float, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class PropertyStatus(str, enum.Enum):
    NEW_PROPERTY = "new_property"
    ENRICHED = "enriched"
    RESEARCHED = "researched"
    WAITING_FOR_CONTRACTS = "waiting_for_contracts"
    COMPLETE = "complete"


class PropertyType(str, enum.Enum):
    HOUSE = "HOUSE"
    APARTMENT = "APARTMENT"
    CONDO = "CONDO"
    TOWNHOUSE = "TOWNHOUSE"
    LAND = "LAND"
    COMMERCIAL = "COMMERCIAL"


class DealType(str, enum.Enum):
    TRADITIONAL = "TRADITIONAL"
    SHORT_SALE = "SHORT_SALE"
    REO = "REO"
    FSBO = "FSBO"
    NEW_CONSTRUCTION = "NEW_CONSTRUCTION"
    WHOLESALE = "WHOLESALE"
    RENTAL = "RENTAL"
    COMMERCIAL = "COMMERCIAL"


class Property(Base):
    __tablename__ = "properties"
    __table_args__ = (
        Index("ix_properties_agent_id", "agent_id"),
        Index("ix_properties_status", "status"),
        Index("ix_properties_pipeline_status", "pipeline_status"),
        Index("ix_properties_agent_status", "agent_id", "status"),
        Index("ix_properties_created_at", "created_at"),
        Index("ix_properties_state_city", "state", "city"),
    )

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
    status = Column(Enum(PropertyStatus, values_callable=lambda x: [e.value for e in x]), default=PropertyStatus.NEW_PROPERTY)
    deal_type = Column(Enum(DealType), nullable=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    # Deal scoring
    deal_score = Column(Float, nullable=True)
    score_grade = Column(String(2), nullable=True)
    score_breakdown = Column(JSON, nullable=True)

    # Auto-enrich pipeline tracking
    pipeline_status = Column(String(20), nullable=True)  # pending, running, completed, failed
    pipeline_started_at = Column(DateTime, nullable=True)
    pipeline_completed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    agent = relationship("Agent", back_populates="properties")
    skip_traces = relationship("SkipTrace", back_populates="property")
    contacts = relationship("Contact", back_populates="property")
    todos = relationship("Todo", back_populates="property")
    contracts = relationship("Contract", back_populates="property")
    zillow_enrichment = relationship("ZillowEnrichment", back_populates="property", uselist=False)
    recap = relationship("PropertyRecap", back_populates="property", uselist=False)
    notes = relationship("PropertyNote", back_populates="property", order_by="PropertyNote.created_at.desc()")
    offers = relationship("Offer", back_populates="property")
