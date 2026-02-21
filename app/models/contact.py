from sqlalchemy import Column, Index, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class ContactRole(str, enum.Enum):
    LAWYER = "lawyer"
    ATTORNEY = "attorney"  # Alias for lawyer
    CONTRACTOR = "contractor"
    INSPECTOR = "inspector"
    APPRAISER = "appraiser"
    MORTGAGE_BROKER = "mortgage_broker"
    LENDER = "lender"
    TITLE_COMPANY = "title_company"
    BUYER = "buyer"
    SELLER = "seller"
    TENANT = "tenant"
    LANDLORD = "landlord"
    PROPERTY_MANAGER = "property_manager"
    HANDYMAN = "handyman"
    PLUMBER = "plumber"
    ELECTRICIAN = "electrician"
    PHOTOGRAPHER = "photographer"
    STAGER = "stager"
    OTHER = "other"


class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = (
        Index("ix_contacts_property_id", "property_id"),
        Index("ix_contacts_role", "role"),
        Index("ix_contacts_property_role", "property_id", "role"),
    )

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)

    # Contact info
    name = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    role = Column(Enum(ContactRole), nullable=False)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    company = Column(String, nullable=True)
    notes = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    property = relationship("Property", back_populates="contacts")
    todos = relationship("Todo", back_populates="contact")
    contracts = relationship("Contract", back_populates="contact")
