import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.property import Property, PropertyStatus, PropertyType
from app.models.agent import Agent
from app.schemas.property import (
    PropertyCreate,
    PropertyUpdate,
    PropertyResponse,
    PropertyCreateFromVoice,
    PropertyCreateFromVoiceResponse,
)
from app.models.property import DealType
from app.services.google_places import google_places_service
from app.services.contract_auto_attach import contract_auto_attach_service
from app.services.deal_type_service import apply_deal_type, get_deal_type_summary
from app.services.scheduled_compliance import schedule_compliance_check

router = APIRouter(prefix="/properties", tags=["properties"])


# Helper function to get WebSocket manager
def get_ws_manager():
    """Get WebSocket manager from main module"""
    try:
        import sys
        if 'app.main' in sys.modules:
            return sys.modules['app.main'].manager
    except:
        pass
    return None


@router.post("/", response_model=PropertyResponse, status_code=201)
async def create_property(property: PropertyCreate, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == property.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    new_property = Property(**property.model_dump())
    db.add(new_property)
    db.commit()
    db.refresh(new_property)

    # Auto-attach required contracts
    contract_auto_attach_service.auto_attach_contracts(db, new_property)

    # Schedule auto compliance check in 20 minutes
    asyncio.create_task(schedule_compliance_check(new_property.id))

    return new_property


@router.post("/voice", response_model=PropertyCreateFromVoiceResponse, status_code=201)
async def create_property_from_voice(
    property: PropertyCreateFromVoice, db: Session = Depends(get_db)
):
    """
    Voice-optimized property creation.
    Uses place_id from address autocomplete to get full address details.
    Returns voice confirmation for the agent to read back.
    """
    agent = db.query(Agent).filter(Agent.id == property.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    address_details = await google_places_service.get_place_details(property.place_id)
    if not address_details:
        raise HTTPException(status_code=400, detail="Invalid address. Please try again.")

    street_address = f"{address_details['street_number']} {address_details['street']}".strip()

    title = property.title or f"{street_address}, {address_details['city']}"

    new_property = Property(
        title=title,
        description=property.description,
        address=street_address,
        city=address_details["city"],
        state=address_details["state"],
        zip_code=address_details["zip_code"],
        price=property.price,
        bedrooms=property.bedrooms,
        bathrooms=property.bathrooms,
        square_feet=property.square_feet,
        lot_size=property.lot_size,
        year_built=property.year_built,
        property_type=property.property_type,
        status=property.status,
        agent_id=property.agent_id,
    )
    db.add(new_property)
    db.commit()
    db.refresh(new_property)

    # Auto-attach required contracts
    attached_contracts = contract_auto_attach_service.auto_attach_contracts(db, new_property)

    # Schedule auto compliance check in 20 minutes
    asyncio.create_task(schedule_compliance_check(new_property.id))

    price_formatted = f"${property.price:,.0f}"
    beds_info = f"{property.bedrooms} bedroom" if property.bedrooms else ""
    baths_info = f"{property.bathrooms} bathroom" if property.bathrooms else ""
    property_details = ", ".join(filter(None, [beds_info, baths_info]))

    voice_confirmation = (
        f"I've created a new listing for {street_address}, "
        f"{address_details['city']}, {address_details['state']}. "
        f"Listed at {price_formatted}"
    )
    if property_details:
        voice_confirmation += f", {property_details}"

    # Mention attached contracts
    if attached_contracts:
        contract_count = len(attached_contracts)
        voice_confirmation += f". I've also attached {contract_count} required contract{'s' if contract_count != 1 else ''} that need to be signed"

    voice_confirmation += ". Is there anything you'd like to change?"

    return PropertyCreateFromVoiceResponse(
        property=new_property,
        voice_confirmation=voice_confirmation,
    )


@router.get("/", response_model=list[PropertyResponse])
def list_properties(
    skip: int = 0,
    limit: int = 100,
    status: PropertyStatus | None = None,
    property_type: PropertyType | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    city: str | None = None,
    bedrooms: int | None = None,
    agent_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = (
        db.query(Property)
        .options(
            joinedload(Property.zillow_enrichment),
            joinedload(Property.skip_traces)
        )
    )

    if status:
        query = query.filter(Property.status == status)
    if property_type:
        query = query.filter(Property.property_type == property_type)
    if min_price is not None:
        query = query.filter(Property.price >= min_price)
    if max_price is not None:
        query = query.filter(Property.price <= max_price)
    if city:
        query = query.filter(Property.city.ilike(f"%{city}%"))
    if bedrooms is not None:
        query = query.filter(Property.bedrooms >= bedrooms)
    if agent_id is not None:
        query = query.filter(Property.agent_id == agent_id)

    properties = query.offset(skip).limit(limit).all()
    return properties


@router.get("/{property_id}", response_model=PropertyResponse)
def get_property(property_id: int, db: Session = Depends(get_db)):
    property = (
        db.query(Property)
        .options(
            joinedload(Property.zillow_enrichment),
            joinedload(Property.skip_traces)
        )
        .filter(Property.id == property_id)
        .first()
    )
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")
    return property


@router.patch("/{property_id}", response_model=PropertyResponse)
async def update_property(
    property_id: int, property: PropertyUpdate, db: Session = Depends(get_db)
):
    from app.services.notification_service import notification_service

    db_property = db.query(Property).filter(Property.id == property_id).first()
    if not db_property:
        raise HTTPException(status_code=404, detail="Property not found")

    # Store old values for change detection
    old_price = db_property.price
    old_status = db_property.status

    update_data = property.model_dump(exclude_unset=True)

    if "agent_id" in update_data:
        agent = db.query(Agent).filter(Agent.id == update_data["agent_id"]).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

    for field, value in update_data.items():
        setattr(db_property, field, value)

    db.commit()
    db.refresh(db_property)

    # Send notifications for changes
    manager = get_ws_manager()

    # Price change notification
    if "price" in update_data and old_price and db_property.price != old_price:
        await notification_service.notify_property_price_change(
            db=db,
            manager=manager,
            property_id=db_property.id,
            property_address=db_property.address,
            old_price=old_price,
            new_price=db_property.price,
            agent_id=db_property.agent_id
        )

    # Status change notification
    if "status" in update_data and old_status and db_property.status != old_status:
        await notification_service.notify_property_status_change(
            db=db,
            manager=manager,
            property_id=db_property.id,
            property_address=db_property.address,
            old_status=old_status.value if old_status else "unknown",
            new_status=db_property.status.value if db_property.status else "unknown",
            agent_id=db_property.agent_id
        )

    return db_property


@router.delete("/{property_id}", status_code=204)
def delete_property(property_id: int, db: Session = Depends(get_db)):
    db_property = db.query(Property).filter(Property.id == property_id).first()
    if not db_property:
        raise HTTPException(status_code=404, detail="Property not found")

    db.delete(db_property)
    db.commit()
    return None


@router.post("/{property_id}/set-deal-type")
def set_property_deal_type(
    property_id: int,
    deal_type_name: str,
    clear_previous: bool = False,
    db: Session = Depends(get_db),
):
    """
    Set a deal type on a property and trigger the full workflow.

    Args:
        clear_previous: If True and switching deal types, removes draft
                        contracts and pending todos from the old deal type
                        before applying the new one. Completed/signed
                        contracts are never removed.
    """
    db_property = db.query(Property).filter(Property.id == property_id).first()
    if not db_property:
        raise HTTPException(status_code=404, detail="Property not found")

    result = apply_deal_type(db, db_property, deal_type_name, clear_previous=clear_previous)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to apply deal type"))

    return result


@router.get("/{property_id}/deal-status")
def get_property_deal_status(
    property_id: int,
    db: Session = Depends(get_db),
):
    """Check deal progress: contracts, checklist, missing contacts."""
    db_property = db.query(Property).filter(Property.id == property_id).first()
    if not db_property:
        raise HTTPException(status_code=404, detail="Property not found")

    return get_deal_type_summary(db, db_property)
