"""Product management API endpoints.

Provides endpoints for:
- Listing available products
- Purchasing products (creates Stripe checkout session)
- Managing user product purchases
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.product import Product, UserProduct, UserProductStatus
from app.models.user import User
from app.services.coolify_provisioning_service import coolify_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ========================================
# Pydantic Models
# ========================================

class ProductResponse(BaseModel):
    """Product listing response"""
    id: int
    name: str
    slug: str
    description: str | None
    price_monthly: float | None
    price_downpayment: float | None
    sku: str | None
    auto_provision: bool
    is_active: bool

    class Config:
        from_attributes = True


class UserProductResponse(BaseModel):
    """User product purchase response"""
    id: int
    user_id: int
    product_id: int
    status: str
    purchase_date: str
    coolify_instance_id: str | None
    expires_at: str | None
    auto_renew: bool
    notes: str | None

    class Config:
        from_attributes = True


class PurchaseRequest(BaseModel):
    """Product purchase request"""
    product_slug: str


class PurchaseResponse(BaseModel):
    """Product purchase response"""
    user_product: UserProductResponse
    checkout_url: str | None = None
    message: str


# ========================================
# Endpoints
# ========================================

@router.get("/products", response_model=List[ProductResponse], status_code=status.HTTP_200_OK)
async def list_products(
    db: Session = Depends(get_db),
):
    """List all active products available for purchase."""
    products = db.query(Product).filter(
        Product.is_active == True
    ).all()

    return products


@router.get("/products/me", response_model=List[UserProductResponse], status_code=status.HTTP_200_OK)
async def list_user_products(
    user_id: int,
    db: Session = Depends(get_db),
):
    """List all products purchased by a user."""
    user_products = db.query(UserProduct).filter(
        UserProduct.user_id == user_id
    ).all()

    return user_products


@router.post("/products/purchase", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED)
async def purchase_product(
    request: PurchaseRequest,
    user_id: int,
    db: Session = Depends(get_db),
):
    """Purchase a product and optionally auto-provision Coolify instance.

    Args:
        request: Purchase request with product_slug
        user_id: ID of the user making the purchase
        db: Database session

    Returns:
        Purchase response with user_product and checkout_url
    """
    # Get product
    product = db.query(Product).filter(
        Product.slug == request.product_slug,
        Product.is_active == True
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{request.product_slug}' not found"
        )

    # Check if user already owns this product
    existing = db.query(UserProduct).filter(
        UserProduct.user_id == user_id,
        UserProduct.product_id == product.id,
        UserProduct.status.in_([UserProductStatus.PENDING, UserProductStatus.ACTIVE])
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You already own this product"
        )

    # Create user product purchase record
    user_product = UserProduct(
        user_id=user_id,
        product_id=product.id,
        status=UserProductStatus.PENDING,
        auto_renew=False,
    )

    db.add(user_product)
    db.commit()
    db.refresh(user_product)

    message = "Purchase created successfully"

    # Auto-provision Coolify instance if enabled
    if product.auto_provision:
        try:
            # Build environment variables for new instance
            environment_vars = {
                "ANTHROPIC_API_KEY": "",  # Will be populated from system config
                "GOOGLE_PLACES_API_KEY": "",
                "RAPIDAPI_KEY": "",
            }

            # Provision instance
            instance_id = await coolify_service.provision_instance(
                product_slug=product.slug,
                environment_vars=environment_vars,
            )

            # Update user product with instance ID
            user_product.coolify_instance_id = instance_id
            user_product.status = UserProductStatus.ACTIVE

            db.commit()
            message = f"Purchase successful! Coolify instance {instance_id} provisioned"

        except Exception as e:
            # Log error but don't fail the purchase
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to auto-provision Coolify instance: {e}")
            message = f"Purchase created! Provisioning failed: {str(e)}"

    return PurchaseResponse(
        user_product=user_product,
        checkout_url=None,  # Will be populated when Stripe is integrated
        message=message,
    )


@router.get("/products/{product_id}", response_model=ProductResponse, status_code=status.HTTP_200_OK)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    """Get details of a specific product."""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_active == True
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )

    return product
