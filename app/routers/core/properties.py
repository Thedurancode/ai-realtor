import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.property import Property, PropertyStatus, PropertyType
from app.models.agent import Agent
from app.models.phone_call import PhoneCall
from app.auth import get_current_agent
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
from app.services.property_pipeline_service import run_auto_enrich_pipeline
from app.utils.websocket import get_ws_manager

router = APIRouter(prefix="/properties", tags=["properties"])


@router.post("/", response_model=PropertyResponse, status_code=201)
async def create_property(
    property: PropertyCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    agent = db.query(Agent).filter(Agent.id == property.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Convert property data to dict, keeping enum instances
    property_data = property.model_dump()
    # Keep enum instances (don't convert to strings) - SQLAlchemy will handle them
    # model_dump() returns enum instances by default in Pydantic v2

    new_property = Property(**property_data)
    new_property.pipeline_status = "pending"
    db.add(new_property)
    db.commit()
    db.refresh(new_property)

    # Auto-attach required contracts
    contract_auto_attach_service.auto_attach_contracts(db, new_property)

    # Check market watchlists for matches
    from app.services.watchlist_service import watchlist_service
    watchlist_service.check_and_notify(db, new_property)

    # Schedule auto compliance check in 20 minutes (use BackgroundTasks)
    background_tasks.add_task(schedule_compliance_check, new_property.id)

    # Kick off auto-enrich pipeline in background
    background_tasks.add_task(run_auto_enrich_pipeline, new_property.id)

    return new_property


@router.post("/voice", response_model=PropertyCreateFromVoiceResponse, status_code=201)
async def create_property_from_voice(
    property: PropertyCreateFromVoice,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
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
        pipeline_status="pending",
    )
    db.add(new_property)
    db.commit()
    db.refresh(new_property)

    # Auto-attach required contracts
    attached_contracts = contract_auto_attach_service.auto_attach_contracts(db, new_property)

    # Check market watchlists for matches
    from app.services.watchlist_service import watchlist_service
    watchlist_service.check_and_notify(db, new_property)

    # Schedule auto compliance check in 20 minutes (use BackgroundTasks)
    background_tasks.add_task(schedule_compliance_check, new_property.id)

    # Kick off auto-enrich pipeline in background
    background_tasks.add_task(run_auto_enrich_pipeline, new_property.id)

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
    include_heartbeat: bool = Query(True, description="Include heartbeat data"),
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

    if not include_heartbeat or not properties:
        return properties

    from app.services.heartbeat_service import heartbeat_service
    try:
        heartbeats = heartbeat_service.get_heartbeats_batch(db, properties)
    except Exception:
        heartbeats = {}

    results = []
    for prop in properties:
        resp = PropertyResponse.model_validate(prop)
        resp.heartbeat = heartbeats.get(prop.id)
        results.append(resp)
    return results


@router.get("/{property_id}", response_model=PropertyResponse)
def get_property(
    property_id: int,
    include_heartbeat: bool = Query(True, description="Include heartbeat data"),
    db: Session = Depends(get_db),
):
    prop = (
        db.query(Property)
        .options(
            joinedload(Property.zillow_enrichment),
            joinedload(Property.skip_traces)
        )
        .filter(Property.id == property_id)
        .first()
    )
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    if not include_heartbeat:
        return prop

    from app.services.heartbeat_service import heartbeat_service
    resp = PropertyResponse.model_validate(prop)
    try:
        resp.heartbeat = heartbeat_service.get_heartbeat(db, property_id)
    except Exception:
        pass
    return resp


@router.get("/{property_id}/heartbeat")
def get_property_heartbeat(property_id: int, db: Session = Depends(get_db)):
    """Get the pipeline heartbeat for a property."""
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    from app.services.heartbeat_service import heartbeat_service
    return heartbeat_service.get_heartbeat(db, property_id)


@router.patch("/{property_id}", response_model=PropertyResponse)
async def update_property(
    property_id: int, property: PropertyUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
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

    from app.services.property_recap_service import regenerate_recap_background
    background_tasks.add_task(regenerate_recap_background, db_property.id, "property_updated")

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


@router.get("/{property_id}/calls")
def get_property_calls(
    property_id: int,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
):
    """
    Get all phone calls for a specific property.

    Returns chronological list of calls with:
    - Call details (provider, direction, status)
    - Recordings and transcriptions
    - Call duration and timestamps
    - AI-generated summaries

    This creates an activity feed of all phone interactions for a property.

    SECURITY: Only returns calls for properties owned by the authenticated agent.
    """
    # Verify property exists and belongs to agent
    db_property = db.query(Property).filter(Property.id == property_id).first()
    if not db_property:
        raise HTTPException(status_code=404, detail="Property not found")
    if db_property.agent_id != current_agent.id:
        raise HTTPException(status_code=403, detail="Not authorized to view calls for this property")

    # Get calls for this property, filtered by agent
    query = db.query(PhoneCall).filter(
        PhoneCall.property_id == property_id,
        PhoneCall.agent_id == current_agent.id  # SECURITY: Agent filtering
    )

    total = query.count()
    calls = query.order_by(PhoneCall.created_at.desc()).offset(offset).limit(limit).all()

    # Format response
    call_list = []
    for call in calls:
        call_list.append({
            "id": call.id,
            "provider": call.provider,
            "direction": call.direction,
            "phone_number": call.phone_number,
            "status": call.status,
            "duration_seconds": call.duration_seconds,
            "created_at": call.created_at.isoformat() if call.created_at else None,
            "started_at": call.started_at.isoformat() if call.started_at else None,
            "ended_at": call.ended_at.isoformat() if call.ended_at else None,
            "recording_url": call.recording_url,
            "transcription": call.transcription,
            "summary": call.summary,
            "intent": call.intent,
            "outcome": call.outcome,
            "cost": call.cost,
        })

    return {
        "property_id": property_id,
        "property_address": f"{db_property.address}, {db_property.city}" if db_property else None,
        "calls": call_list,
        "total": total,
        "limit": limit,
        "offset": offset,
    }
