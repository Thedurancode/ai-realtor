"""Product models for SaaS platform.

Allows management of purchasable products/services with
automatic Coolify instance provisioning.
"""

from sqlalchemy import Column, String, DateTime, Text, Float, Integer, Boolean, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class AutoProvision(Enum):
    """Whether product is auto-provisioned after purchase"""
    DISABLED = "disabled"
    ENABLED = "enabled"


class ProductStatus(Enum):
    """Product status"""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class Product(Base):
    """Products that can be purchased by users."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    price_monthly = Column(Float(10, 2), nullable=True)
    price_downpayment = Column(Float(10, 2), nullable=True)
    sku = Column(String(100), nullable=True)

    # Coolify configuration
    coolify_config = Column(JSON, nullable=True)  # Stores instance settings

    # Auto-provisioning
    auto_provision = Column(Boolean, default=False, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<Product(id={self.id}, name={self.name}, slug={self.slug})>"


class UserProductStatus(Enum):
    """User product purchase status"""
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class UserProduct(Base):
    """User's purchased products with Coolify instance links."""
    __tablename__ = "user_products"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)

    # Status and timestamps
    status = Column(String(50), default=UserProductStatus.PENDING, nullable=False, index=True)
    purchase_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Coolify instance linkage
    coolify_instance_id = Column(String(255), nullable=True, index=True)

    # Expiration and renewal
    expires_at = Column(DateTime(timezone=True), nullable=True)
    subscription_cancelled_at = Column(DateTime(timezone=True), nullable=True)

    # Auto-renewal
    auto_renew = Column(Boolean, default=False, nullable=False)

    # Notes
    notes = Column(Text, nullable=True)

    # Relationships
    product = relationship("Product", back_populates="name")
    user = relationship("User", back_populates="name")

    def __repr__(self):
        return f"<UserProduct(user_id={self.user_id}, product={self.product_id}, status={self.status})>"
