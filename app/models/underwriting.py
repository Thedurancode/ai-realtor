from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Underwriting(Base):
    __tablename__ = "underwriting"

    id = Column(Integer, primary_key=True, index=True)
    research_property_id = Column(Integer, ForeignKey("research_properties.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("agentic_jobs.id"), nullable=False, index=True)

    strategy = Column(String(32), nullable=False, default="wholesale")
    assumptions = Column(JSON, nullable=True)

    arv_low = Column(Float, nullable=True)
    arv_base = Column(Float, nullable=True)
    arv_high = Column(Float, nullable=True)

    rent_low = Column(Float, nullable=True)
    rent_base = Column(Float, nullable=True)
    rent_high = Column(Float, nullable=True)

    rehab_tier = Column(String(16), nullable=False, default="medium")
    rehab_low = Column(Float, nullable=True)
    rehab_high = Column(Float, nullable=True)

    offer_low = Column(Float, nullable=True)
    offer_base = Column(Float, nullable=True)
    offer_high = Column(Float, nullable=True)

    fees = Column(JSON, nullable=True)
    sensitivity = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    research_property = relationship("ResearchProperty", back_populates="underwriting_items")
    job = relationship("AgenticJob", back_populates="underwriting_items")
