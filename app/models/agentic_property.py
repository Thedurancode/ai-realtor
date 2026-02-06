from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ResearchProperty(Base):
    __tablename__ = "research_properties"

    id = Column(Integer, primary_key=True, index=True)
    stable_key = Column(String(128), nullable=False, unique=True, index=True)

    raw_address = Column(String, nullable=False)
    normalized_address = Column(String, nullable=False)
    city = Column(String, nullable=True)
    state = Column(String(2), nullable=True)
    zip_code = Column(String(10), nullable=True)
    apn = Column(String, nullable=True)

    geo_lat = Column(Float, nullable=True)
    geo_lng = Column(Float, nullable=True)

    latest_profile = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    jobs = relationship("AgenticJob", back_populates="research_property")
    evidence_items = relationship("EvidenceItem", back_populates="research_property")
    comp_sales = relationship("CompSale", back_populates="research_property")
    comp_rentals = relationship("CompRental", back_populates="research_property")
    underwriting_items = relationship("Underwriting", back_populates="research_property")
    risk_scores = relationship("RiskScore", back_populates="research_property")
    dossiers = relationship("Dossier", back_populates="research_property")
