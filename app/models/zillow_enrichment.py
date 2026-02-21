"""
Zillow enrichment model for storing comprehensive property data from Zillow API
"""
from sqlalchemy import Column, Index, Integer, String, Float, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ZillowEnrichment(Base):
    """Store Zillow API enrichment data for properties"""
    __tablename__ = "zillow_enrichments"
    __table_args__ = (
        Index("ix_zillow_enrichments_property_id", "property_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)

    # Zillow identifiers
    zpid = Column(Integer, nullable=True)  # Zillow Property ID

    # Valuation data
    zestimate = Column(Float, nullable=True)
    zestimate_low = Column(Float, nullable=True)
    zestimate_high = Column(Float, nullable=True)
    rent_zestimate = Column(Float, nullable=True)

    # Property details
    living_area = Column(Float, nullable=True)
    lot_size = Column(Float, nullable=True)
    lot_area_units = Column(String, nullable=True)
    year_built = Column(Integer, nullable=True)
    home_type = Column(String, nullable=True)
    home_status = Column(String, nullable=True)

    # Listing data
    days_on_zillow = Column(Integer, nullable=True)
    page_view_count = Column(Integer, nullable=True)
    favorite_count = Column(Integer, nullable=True)

    # Tax information
    property_tax_rate = Column(Float, nullable=True)
    annual_tax_amount = Column(Float, nullable=True)

    # URLs
    hdp_url = Column(String, nullable=True)  # Home detail page URL
    zillow_url = Column(String, nullable=True)

    # Photos (array of photo URLs)
    photos = Column(JSON, nullable=True)

    # Description
    description = Column(String(10000), nullable=True)

    # Comprehensive data
    schools = Column(JSON, nullable=True)  # School information
    tax_history = Column(JSON, nullable=True)  # Tax history array
    price_history = Column(JSON, nullable=True)  # Price history array
    reso_facts = Column(JSON, nullable=True)  # RESO standard facts

    # Full raw response for reference
    raw_response = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    property = relationship("Property", back_populates="zillow_enrichment")


# Update Property model to add zillow_enrichment relationship
# This will be added to app/models/property.py
