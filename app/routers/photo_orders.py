"""
Property Photo Ordering API Routes

Provides endpoints for:
- Creating photo orders
- Submitting to providers (ProxyPics, BoxBrownie, etc.)
- Tracking order status
- Managing deliverables
- Order templates
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.property import Property
from app.models.photo_order import PhotoOrder, PhotoOrderTemplate, PhotoProvider
from app.schemas.photo_order import (
    PhotoOrderCreate,
    PhotoOrderUpdate,
    PhotoOrderResponse,
    PhotoOrderSummary,
    PhotoOrderSubmit,
    PhotoOrderItemCreate,
    PhotoOrderItemResponse,
    PhotoOrderDeliverableResponse,
    PhotoOrderDeliverableUpdate,
    PhotoOrderTemplateCreate,
    PhotoOrderTemplateResponse,
    PhotoOrderVoiceSummary,
    PhotoServiceAvailability
)
from app.services.photo_order_service import (
    PhotoOrderService,
    PhotoOrderTemplateService
)

router = APIRouter(prefix="/photo-orders", tags=["photo-orders"])


# =============================================================================
# PHOTO ORDERS
# =============================================================================

@router.post("/", response_model=PhotoOrderResponse, status_code=201)
def create_photo_order(
    payload: PhotoOrderCreate,
    agent_id: int = Query(..., description="Agent ID"),
    db: Session = Depends(get_db)
):
    """
    Create a new photo order

    Automatically populates address from property if not provided.
    Estimates cost based on services requested.
    """
    try:
        # Verify property exists
        property_obj = db.query(Property).filter(Property.id == payload.property_id).first()
        if not property_obj:
            raise HTTPException(status_code=404, detail=f"Property {payload.property_id} not found")

        service = PhotoOrderService(db)
        order = service.create_order(payload, property_obj, agent_id)
        return PhotoOrderResponse.model_validate(order)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[PhotoOrderSummary])
def list_photo_orders(
    property_id: Optional[int] = Query(None, description="Filter by property"),
    status: Optional[str] = Query(None, description="Filter by status"),
    provider: Optional[str] = Query(None, description="Filter by provider"),
    agent_id: Optional[int] = Query(None, description="Filter by agent"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List photo orders with optional filters

    Supports filtering by property, status, provider, and agent.
    """
    query = db.query(PhotoOrder)

    if property_id:
        query = query.filter(PhotoOrder.property_id == property_id)
    if status:
        query = query.filter(PhotoOrder.order_status == status)
    if provider:
        query = query.filter(PhotoOrder.provider == provider)
    if agent_id:
        query = query.filter(PhotoOrder.agent_id == agent_id)

    orders = (
        query
        .order_by(PhotoOrder.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    # Add property addresses
    result = []
    for order in orders:
        order_dict = PhotoOrderSummary.model_validate(order).model_dump()
        property_obj = db.query(Property).filter(Property.id == order.property_id).first()
        if property_obj:
            order_dict["property_address"] = property_obj.address
        result.append(PhotoOrderSummary(**order_dict))

    return result


@router.get("/{order_id}", response_model=PhotoOrderResponse)
def get_photo_order(order_id: int, db: Session = Depends(get_db)):
    """Get details of a specific photo order"""
    order = db.query(PhotoOrder).filter(PhotoOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Photo order {order_id} not found")
    return PhotoOrderResponse.model_validate(order)


@router.put("/{order_id}", response_model=PhotoOrderResponse)
def update_photo_order(
    order_id: int,
    payload: PhotoOrderUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a photo order

    Only draft orders can be updated.
    """
    order = db.query(PhotoOrder).filter(PhotoOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Photo order {order_id} not found")

    if order.order_status not in ["draft", "pending"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot update order in status {order.order_status.value}"
        )

    # Update fields
    if payload.requested_date is not None:
        order.requested_date = payload.requested_date
    if payload.time_slot_preference is not None:
        order.time_slot_preference = payload.time_slot_preference
    if payload.special_instructions is not None:
        order.special_instructions = payload.special_instructions
    if payload.contact_name is not None:
        order.contact_name = payload.contact_name
    if payload.contact_phone is not None:
        order.contact_phone = payload.contact_phone
    if payload.contact_email is not None:
        order.contact_email = payload.contact_email
    if payload.admin_notes is not None:
        order.admin_notes = payload.admin_notes
    if payload.services is not None:
        order.services_requested = payload.services
        # Recalculate estimated cost
        service = PhotoOrderService(db)
        order.estimated_cost = service._estimate_cost(payload.services)

    db.commit()
    db.refresh(order)
    return PhotoOrderResponse.model_validate(order)


@router.post("/{order_id}/submit", response_model=PhotoOrderResponse)
async def submit_photo_order(
    order_id: int,
    payload: PhotoOrderSubmit = PhotoOrderSubmit(),
    db: Session = Depends(get_db)
):
    """
    Submit photo order to provider

    Sends the order to ProxyPics, BoxBrownie, or other configured provider.
    """
    try:
        service = PhotoOrderService(db)
        order = await service.submit_order(order_id, payload.confirm_submit)
        return PhotoOrderResponse.model_validate(order)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit order: {str(e)}")


@router.get("/{order_id}/status")
def get_order_status(order_id: int, db: Session = Depends(get_db)):
    """Get current status of a photo order"""
    try:
        service = PhotoOrderService(db)
        status = service.get_order_status(order_id)
        return status

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{order_id}/sync", response_model=PhotoOrderResponse)
async def sync_order_status(
    order_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Sync order status with provider

    Fetches latest status from ProxyPics or other provider.
    Updates deliverables if photos are ready.
    """
    try:
        service = PhotoOrderService(db)
        order = await service.sync_order_status(order_id)
        return PhotoOrderResponse.model_validate(order)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync order: {str(e)}")


@router.post("/{order_id}/cancel", response_model=PhotoOrderResponse)
def cancel_photo_order(
    order_id: int,
    reason: Optional[str] = Query(None, description="Cancellation reason"),
    db: Session = Depends(get_db)
):
    """
    Cancel a photo order

    Can only cancel draft, pending, or confirmed orders.
    """
    try:
        service = PhotoOrderService(db)
        order = service.cancel_order(order_id, reason)
        return PhotoOrderResponse.model_validate(order)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{order_id}/voice-summary", response_model=PhotoOrderVoiceSummary)
def get_order_voice_summary(order_id: int, db: Session = Depends(get_db)):
    """
    Get voice-friendly summary of order

    Natural language summary suitable for text-to-speech.
    """
    try:
        service = PhotoOrderService(db)
        return service.get_voice_summary(order_id)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# ORDER ITEMS
# =============================================================================

@router.get("/{order_id}/items", response_model=List[PhotoOrderItemResponse])
def list_order_items(order_id: int, db: Session = Depends(get_db)):
    """List all items in a photo order"""
    order = db.query(PhotoOrder).filter(PhotoOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Photo order {order_id} not found")

    from app.models.photo_order import PhotoOrderItem
    items = (
        db.query(PhotoOrderItem)
        .filter(PhotoOrderItem.order_id == order_id)
        .all()
    )

    return [PhotoOrderItemResponse.model_validate(item) for item in items]


@router.post("/{order_id}/items", response_model=PhotoOrderItemResponse, status_code=201)
def add_order_item(
    order_id: int,
    payload: PhotoOrderItemCreate,
    db: Session = Depends(get_db)
):
    """
    Add an item to a photo order

    Only draft orders can accept new items.
    """
    order = db.query(PhotoOrder).filter(PhotoOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Photo order {order_id} not found")

    if order.order_status != "draft":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot add items to order in status {order.order_status.value}"
        )

    from app.models.photo_order import PhotoOrderItem

    item = PhotoOrderItem(
        order_id=order_id,
        service_type=payload.service_type,
        service_name=payload.service_name,
        description=payload.description,
        quantity=payload.quantity,
        room_name=payload.room_name,
        floor=payload.floor,
        enhancement_options=payload.enhancement_options,
        unit_price=payload.unit_price
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return PhotoOrderItemResponse.model_validate(item)


# =============================================================================
# DELIVERABLES
# =============================================================================

@router.get("/{order_id}/deliverables", response_model=List[PhotoOrderDeliverableResponse])
def list_deliverables(
    order_id: int,
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    db: Session = Depends(get_db)
):
    """List all deliverables for an order"""
    order = db.query(PhotoOrder).filter(PhotoOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Photo order {order_id} not found")

    from app.models.photo_order import PhotoOrderDeliverable

    query = db.query(PhotoOrderDeliverable).filter(PhotoOrderDeliverable.order_id == order_id)

    if file_type:
        query = query.filter(PhotoOrderDeliverable.file_type == file_type)

    deliverables = query.order_by(PhotoOrderDeliverable.sequence).all()

    return [PhotoOrderDeliverableResponse.model_validate(d) for d in deliverables]


@router.put("/deliverables/{deliverable_id}", response_model=PhotoOrderDeliverableResponse)
def update_deliverable(
    deliverable_id: int,
    payload: PhotoOrderDeliverableUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a deliverable

    Can mark as approved, feature as primary photo, etc.
    """
    from app.models.photo_order import PhotoOrderDeliverable

    deliverable = (
        db.query(PhotoOrderDeliverable)
        .filter(PhotoOrderDeliverable.id == deliverable_id)
        .first()
    )

    if not deliverable:
        raise HTTPException(status_code=404, detail=f"Deliverable {deliverable_id} not found")

    if payload.is_approved is not None:
        deliverable.is_approved = payload.is_approved
    if payload.is_featured is not None:
        deliverable.is_featured = payload.is_featured
    if payload.room_name is not None:
        deliverable.room_name = payload.room_name
    if payload.sequence is not None:
        deliverable.sequence = payload.sequence

    db.commit()
    db.refresh(deliverable)

    return PhotoOrderDeliverableResponse.model_validate(deliverable)


# =============================================================================
# TEMPLATES
# =============================================================================

@router.post("/templates/", response_model=PhotoOrderTemplateResponse, status_code=201)
def create_template(
    payload: PhotoOrderTemplateCreate,
    agent_id: int = Query(..., description="Agent ID"),
    db: Session = Depends(get_db)
):
    """Create a new order template"""
    try:
        service = PhotoOrderTemplateService(db)
        template = service.create_template(payload, agent_id)
        return PhotoOrderTemplateResponse.model_validate(template)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/templates/", response_model=List[PhotoOrderTemplateResponse])
def list_templates(
    agent_id: int = Query(..., description="Agent ID"),
    property_type: Optional[str] = Query(None, description="Filter by property type"),
    db: Session = Depends(get_db)
):
    """List order templates for an agent"""
    service = PhotoOrderTemplateService(db)
    templates = service.get_templates_for_property(agent_id, property_type or "")
    return [PhotoOrderTemplateResponse.model_validate(t) for t in templates]


@router.get("/templates/{template_id}", response_model=PhotoOrderTemplateResponse)
def get_template(template_id: int, db: Session = Depends(get_db)):
    """Get a specific template"""
    template = (
        db.query(PhotoOrderTemplate)
        .filter(PhotoOrderTemplate.id == template_id)
        .first()
    )

    if not template:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")

    return PhotoOrderTemplateResponse.model_validate(template)


@router.post("/templates/{template_id}/apply")
def apply_template(
    template_id: int,
    property_id: int = Query(..., description="Property to apply template to"),
    db: Session = Depends(get_db)
):
    """
    Apply a template to create a new order

    Returns pre-filled order data ready for submission.
    """
    try:
        service = PhotoOrderTemplateService(db)
        return service.apply_template(template_id, property_id)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# SERVICE AVAILABILITY
# =============================================================================

@router.get("/services/availability", response_model=PhotoServiceAvailability)
def get_service_availability(
    property_id: int,
    provider: str = Query("proxypics", description="Provider to check"),
    db: Session = Depends(get_db)
):
    """
    Check service availability for a property

    Returns available services, estimated costs, and recommendations.
    """
    property_obj = db.query(Property).filter(Property.id == property_id).first()
    if not property_obj:
        raise HTTPException(status_code=404, detail=f"Property {property_id} not found")

    # Check for existing orders
    existing_orders = (
        db.query(PhotoOrder)
        .filter(
            PhotoOrder.property_id == property_id,
            PhotoOrder.order_status.in_(["draft", "pending", "confirmed", "in_progress"])
        )
        .count()
    )

    # Available services with base pricing
    services_available = [
        "hdr_interior",
        "exterior_day",
        "exterior_twilight",
        "aerial_drone",
        "panoramic_360",
        "virtual_tour_3d",
        "walkthrough_video",
        "virtual_staging",
        "floor_plan"
    ]

    estimated_costs = {
        "hdr_interior": 15.0,
        "exterior_day": 10.0,
        "exterior_twilight": 20.0,
        "aerial_drone": 50.0,
        "panoramic_360": 25.0,
        "virtual_tour_3d": 100.0,
        "walkthrough_video": 75.0,
        "virtual_staging": 30.0,
        "floor_plan": 40.0
    }

    # Recommend package based on property type
    recommended_package = None
    if property_obj.property_type == "HOUSE":
        recommended_package = "basic_listing"
    elif property_obj.property_type == "CONDO":
        recommended_package = "condo essentials"
    elif property_obj.price > 500000:
        recommended_package = "premium"

    can_order = existing_orders == 0
    reason = "No active orders for this property" if can_order else f"Property has {existing_orders} active order(s)"

    return PhotoServiceAvailability(
        property_id=property_id,
        services_available=services_available,
        estimated_costs=estimated_costs,
        recommended_package=recommended_package,
        current_orders=existing_orders,
        can_order=can_order,
        reason=reason
    )


# =============================================================================
# PROPERTY SUMMARY
# =============================================================================

@router.get("/property/{property_id}/summary")
def get_property_photo_summary(property_id: int, db: Session = Depends(get_db)):
    """
    Get photo ordering summary for a property

    Returns all orders, total spend, delivery status, etc.
    """
    property_obj = db.query(Property).filter(Property.id == property_id).first()
    if not property_obj:
        raise HTTPException(status_code=404, detail=f"Property {property_id} not found")

    orders = (
        db.query(PhotoOrder)
        .filter(PhotoOrder.property_id == property_id)
        .order_by(PhotoOrder.created_at.desc())
        .all()
    )

    total_orders = len(orders)
    total_spend = sum(o.actual_cost or o.estimated_cost or 0 for o in orders)
    total_photos = sum(o.delivery_count or 0 for o in orders)

    active_orders = [o for o in orders if o.order_status.value in ["draft", "pending", "confirmed", "in_progress"]]
    completed_orders = [o for o in orders if o.order_status.value == "completed"]

    return {
        "property_id": property_id,
        "property_address": property_obj.address,
        "total_orders": total_orders,
        "active_orders": len(active_orders),
        "completed_orders": len(completed_orders),
        "total_spend": round(total_spend, 2),
        "total_photos_delivered": total_photos,
        "latest_order": PhotoOrderSummary.model_validate(orders[0]).model_dump() if orders else None,
        "can_order": len(active_orders) == 0
    }
