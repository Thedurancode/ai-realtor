"""
Contract Template Configuration Model

This model stores contract template configurations that should be
automatically attached to properties based on state, property type, etc.
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy import DateTime
import enum

from app.database import Base


class ContractCategory(str, enum.Enum):
    """Contract categories"""
    LISTING = "listing"
    PURCHASE = "purchase"
    DISCLOSURE = "disclosure"
    INSPECTION = "inspection"
    LEASE = "lease"
    ADDENDUM = "addendum"
    OTHER = "other"


class ContractRequirement(str, enum.Enum):
    """When contract is required"""
    REQUIRED = "required"  # Must be signed before closing
    RECOMMENDED = "recommended"  # Should be signed
    OPTIONAL = "optional"  # Nice to have


class ContractTemplate(Base):
    """
    Contract template configurations that define which contracts
    should be automatically attached to properties.

    Example: All NY properties require a Property Condition Disclosure form
    """
    __tablename__ = "contract_templates"

    id = Column(Integer, primary_key=True, index=True)

    # Template info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(Enum(ContractCategory), nullable=False)
    requirement = Column(Enum(ContractRequirement), default=ContractRequirement.RECOMMENDED)

    # DocuSeal integration
    docuseal_template_id = Column(String(100), nullable=True)
    docuseal_template_name = Column(String(255), nullable=True)

    # Applicability filters
    state = Column(String(2), nullable=True, index=True)  # e.g., "NY", "CA", null=all states
    city = Column(String(100), nullable=True)  # null=all cities in state
    property_type_filter = Column(JSON, nullable=True)  # ["house", "condo"] or null=all types

    # Price filters
    min_price = Column(Integer, nullable=True)  # Only properties >= this price
    max_price = Column(Integer, nullable=True)  # Only properties <= this price

    # Deal type filter
    deal_type_filter = Column(JSON, nullable=True)  # ["short_sale", "reo"] or null=all deal types

    # Configuration
    auto_attach_on_create = Column(Boolean, default=True)  # Auto-attach when property created
    auto_send = Column(Boolean, default=False)  # Auto-send to contacts when attached

    # Recipient configuration
    default_recipient_role = Column(String(50), nullable=True)  # "seller", "buyer", "lawyer", etc.
    required_signer_roles = Column(JSON, nullable=True)  # ["buyer", "seller"] - roles that must sign this contract
    message_template = Column(Text, nullable=True)  # Default message when sending

    # Status
    is_active = Column(Boolean, default=True, index=True)
    priority = Column(Integer, default=0)  # Higher priority = shown first

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def applies_to_property(self, property) -> bool:
        """Check if this template applies to a given property"""
        # Check state
        if self.state and property.state != self.state:
            return False

        # Check city
        if self.city and property.city != self.city:
            return False

        # Check property type
        if self.property_type_filter:
            property_type_str = property.property_type.value if property.property_type else None
            if property_type_str not in self.property_type_filter:
                return False

        # Check price range
        if self.min_price and property.price < self.min_price:
            return False
        if self.max_price and property.price > self.max_price:
            return False

        # Check deal type
        if self.deal_type_filter:
            deal_type_str = property.deal_type.value if property.deal_type else None
            if deal_type_str not in self.deal_type_filter:
                return False

        return True
