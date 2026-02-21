from sqlalchemy import Boolean, Column, Index, Integer, String, Float, Date, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class CompSale(Base):
    __tablename__ = "comps_sales"
    __table_args__ = (
        Index("ix_comps_sales_current", "job_id", "is_current"),
    )

    id = Column(Integer, primary_key=True, index=True)
    research_property_id = Column(Integer, ForeignKey("research_properties.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("agentic_jobs.id"), nullable=False, index=True)

    address = Column(String, nullable=False)
    distance_mi = Column(Float, nullable=True)
    sale_date = Column(Date, nullable=True)
    sale_price = Column(Float, nullable=True)
    sqft = Column(Integer, nullable=True)
    beds = Column(Integer, nullable=True)
    baths = Column(Float, nullable=True)
    year_built = Column(Integer, nullable=True)
    similarity_score = Column(Float, nullable=False)
    source_url = Column(String(1000), nullable=False)

    details = Column(JSON, nullable=True)
    is_current = Column(Boolean, nullable=False, server_default="true")
    superseded_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    research_property = relationship("ResearchProperty", back_populates="comp_sales")
    job = relationship("AgenticJob", back_populates="comp_sales")
