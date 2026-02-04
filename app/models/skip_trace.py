from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class SkipTrace(Base):
    __tablename__ = "skip_traces"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)

    # Owner information
    owner_name = Column(String, nullable=True)
    owner_first_name = Column(String, nullable=True)
    owner_last_name = Column(String, nullable=True)

    # Contact information (stored as JSON arrays for multiple numbers/emails)
    phone_numbers = Column(JSON, default=list)  # [{"number": "...", "type": "mobile", "status": "valid"}]
    emails = Column(JSON, default=list)  # [{"email": "...", "type": "personal"}]

    # Mailing address (if different from property)
    mailing_address = Column(String, nullable=True)
    mailing_city = Column(String, nullable=True)
    mailing_state = Column(String, nullable=True)
    mailing_zip = Column(String, nullable=True)

    # Additional data
    raw_response = Column(JSON, nullable=True)  # Store full API response for debugging

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    property = relationship("Property", back_populates="skip_traces")
