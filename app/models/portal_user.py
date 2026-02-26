"""
Portal User Model - Customer Portal Authentication
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class PortalUser(Base):
    """
    Customer portal users (buyers, sellers, tenants)
    Can view their own properties, contracts, and documents
    """
    __tablename__ = "portal_users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)

    # Profile
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    company = Column(String, nullable=True)

    # Role and Type
    role = Column(String, nullable=False, default="client")  # client, admin
    client_type = Column(String, nullable=True)  # buyer, seller, tenant, landlord

    # Agent who invited this client
    invited_by_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime, nullable=True)

    # Preferences
    notification_email = Column(Boolean, default=True)
    notification_sms = Column(Boolean, default=False)
    notification_push = Column(Boolean, default=True)

    # Relationships
    agent = relationship("Agent", back_populates="portal_users")
    property_access = relationship("PropertyAccess", back_populates="portal_user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PortalUser(id={self.id}, email={self.email}, role={self.role})>"


class PropertyAccess(Base):
    """
    Grants portal users access to specific properties
    Links clients to the properties they're involved with
    """
    __tablename__ = "property_access"

    id = Column(Integer, primary_key=True, index=True)
    portal_user_id = Column(Integer, ForeignKey("portal_users.id"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)

    # Access level and relationship type
    access_level = Column(String, default="view")  # view, sign, full
    relationship_type = Column(String, nullable=True)  # buyer, seller, tenant, landlord, co_buyer

    # Permissions (granular)
    can_view_details = Column(Boolean, default=True)
    can_view_contracts = Column(Boolean, default=True)
    can_view_documents = Column(Boolean, default=True)
    can_sign_contracts = Column(Boolean, default=False)
    can_view_price = Column(Boolean, default=False)  # Hide price for some clients

    # Status
    is_active = Column(Boolean, default=True)
    invited_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    accepted_at = Column(DateTime, nullable=True)

    # Relationships
    portal_user = relationship("PortalUser", back_populates="property_access")
    property = relationship("Property", back_populates="access_list")

    def __repr__(self):
        return f"<PropertyAccess(user_id={self.portal_user_id}, property_id={self.property_id}, level={self.access_level})>"


class PortalActivity(Base):
    """
    Track all portal user activity for audit trail
    """
    __tablename__ = "portal_activity"

    id = Column(Integer, primary_key=True, index=True)
    portal_user_id = Column(Integer, ForeignKey("portal_users.id"), nullable=False)

    # Activity details
    action = Column(String, nullable=False)  # login, view_property, sign_contract, etc.
    resource_type = Column(String, nullable=True)  # property, contract, document
    resource_id = Column(Integer, nullable=True)

    # Metadata
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    extra_metadata = Column(Text, nullable=True)  # JSON string for extra data

    # Timestamp
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationship
    portal_user = relationship("PortalUser")

    def __repr__(self):
        return f"<PortalActivity(user_id={self.portal_user_id}, action={self.action})>"
