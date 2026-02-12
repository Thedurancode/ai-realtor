"""
Context-aware endpoints for natural conversation flow
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.rate_limit import limiter
from app.models.property import Property
from app.services.conversation_context import (
    get_context,
    hydrate_context_from_graph,
    persist_context_to_graph,
    resolve_property_reference,
)
from app.services.skip_trace import skip_trace_service
from app.models.skip_trace import SkipTrace
from app.services.zillow_enrichment import zillow_enrichment_service
from app.models.zillow_enrichment import ZillowEnrichment
from app.services.memory_graph import MemoryRef, memory_graph_service

router = APIRouter(prefix="/context", tags=["context"])


# Helper function to get WebSocket manager (avoids circular import)
def get_ws_manager():
    """Get WebSocket manager from main module"""
    try:
        import sys
        if 'app.main' in sys.modules:
            return sys.modules['app.main'].manager
    except:
        pass
    return None


class ContextPropertyCreate(BaseModel):
    """Create property and remember it in context"""
    place_id: str
    price: float
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    agent_id: int
    session_id: str = "default"


class ContextSkipTraceRequest(BaseModel):
    """Skip trace with context awareness"""
    property_ref: Optional[str] = None  # "this", "that", address, or ID
    session_id: str = "default"


class ContextResponse(BaseModel):
    """Response with context awareness"""
    success: bool
    message: str
    data: dict
    context_summary: dict


@router.get("/summary")
def get_context_summary(session_id: str = "default", db: Session = Depends(get_db)):
    """
    Get current conversation context.

    Shows what the system remembers about recent actions.
    """
    context = hydrate_context_from_graph(db=db, session_id=session_id)
    graph_summary = memory_graph_service.get_session_summary(db=db, session_id=session_id)
    return {
        "context": context.get_summary(),
        "persistent_memory": graph_summary,
        "status": "stale" if context.is_stale() else "active"
    }


@router.post("/property/create", response_model=ContextResponse)
async def create_property_with_context(
    request: ContextPropertyCreate,
    db: Session = Depends(get_db)
):
    """
    Create property and remember it for follow-up commands.

    After calling this, you can say:
    - "Skip trace this property"
    - "Add a contact for this property"
    - "Create a contract for this property"
    """
    from app.services.google_places import google_places_service
    from app.models.agent import Agent

    # Verify agent exists
    agent = db.query(Agent).filter(Agent.id == request.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Get address details
    address_details = await google_places_service.get_place_details(request.place_id)
    if not address_details:
        raise HTTPException(status_code=400, detail="Invalid address")

    street_address = f"{address_details['street_number']} {address_details['street']}".strip()

    # Create property
    new_property = Property(
        title=f"{street_address}, {address_details['city']}",
        address=street_address,
        city=address_details["city"],
        state=address_details["state"],
        zip_code=address_details["zip_code"],
        price=request.price,
        bedrooms=request.bedrooms,
        bathrooms=request.bathrooms,
        agent_id=request.agent_id,
        status="available",
        property_type="house"
    )
    db.add(new_property)
    db.commit()
    db.refresh(new_property)

    # Remember in context
    context = get_context(request.session_id)
    context.set_last_property(new_property.id, street_address)
    memory_graph_service.remember_property(
        db=db,
        session_id=request.session_id,
        property_id=new_property.id,
        address=street_address,
        city=address_details["city"],
        state=address_details["state"],
    )
    persist_context_to_graph(db=db, session_id=request.session_id)
    db.commit()

    return ContextResponse(
        success=True,
        message=f"Created property at {street_address}. You can now say 'skip trace this property'",
        data={
            "property_id": new_property.id,
            "address": street_address,
            "city": address_details["city"],
            "state": address_details["state"],
            "price": request.price
        },
        context_summary=context.get_summary()
    )


@router.post("/skip-trace", response_model=ContextResponse)
@limiter.limit("5/minute")
async def skip_trace_with_context(
    request: Request,
    body: ContextSkipTraceRequest,
    db: Session = Depends(get_db)
):
    """
    Skip trace using context awareness.

    Examples:
    - property_ref: null → Uses last property from context
    - property_ref: "this" → Uses last property
    - property_ref: "312 eisler" → Searches by address
    - property_ref: "2" → Uses property ID 2
    """
    # Resolve property reference
    property_id = resolve_property_reference(
        body.property_ref,
        body.session_id
    )

    if not property_id:
        # Try to search by address if provided
        if body.property_ref:
            query = body.property_ref.lower()
            property = (
                db.query(Property)
                .filter(Property.address.ilike(f"%{query}%"))
                .first()
            )
            if property:
                property_id = property.id

    if not property_id:
        raise HTTPException(
            status_code=400,
            detail="No property reference found. Please specify 'this property', an address, or property ID"
        )

    # Get property
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    # Check for existing skip trace
    existing = (
        db.query(SkipTrace)
        .filter(SkipTrace.property_id == property.id)
        .order_by(SkipTrace.created_at.desc())
        .first()
    )

    if existing:
        skip_trace = existing
    else:
        # Run skip trace
        result = await skip_trace_service.skip_trace(
            address=property.address,
            city=property.city,
            state=property.state,
            zip_code=property.zip_code,
        )

        # Save result
        skip_trace = SkipTrace(
            property_id=property.id,
            owner_name=result["owner_name"],
            owner_first_name=result["owner_first_name"],
            owner_last_name=result["owner_last_name"],
            phone_numbers=result["phone_numbers"],
            emails=result["emails"],
            mailing_address=result["mailing_address"],
            mailing_city=result["mailing_city"],
            mailing_state=result["mailing_state"],
            mailing_zip=result["mailing_zip"],
            raw_response=result["raw_response"],
        )
        db.add(skip_trace)
        db.commit()
        db.refresh(skip_trace)

    # Remember in context
    context = get_context(body.session_id)
    context.set_last_property(property.id, property.address)
    context.set_last_skip_trace(skip_trace.id, property.id)
    memory_graph_service.remember_property(
        db=db,
        session_id=body.session_id,
        property_id=property.id,
        address=property.address,
        city=property.city,
        state=property.state,
    )
    if skip_trace.owner_name:
        memory_graph_service.upsert_node(
            db=db,
            session_id=body.session_id,
            node_type="owner",
            node_key=f"skip_trace:{skip_trace.id}",
            summary=skip_trace.owner_name,
            payload={
                "owner_name": skip_trace.owner_name,
                "property_id": property.id,
                "skip_trace_id": skip_trace.id,
            },
            importance=0.85,
        )
        memory_graph_service.upsert_edge(
            db=db,
            session_id=body.session_id,
            source=MemoryRef("owner", f"skip_trace:{skip_trace.id}"),
            target=MemoryRef("property", str(property.id)),
            relation="owns",
            weight=0.75,
        )
    memory_graph_service.remember_session_state(
        db=db,
        session_id=body.session_id,
        key="last_skip_trace_id",
        value=skip_trace.id,
    )
    persist_context_to_graph(db=db, session_id=body.session_id)
    db.commit()

    return ContextResponse(
        success=True,
        message=f"Found owner: {skip_trace.owner_name} for {property.address}",
        data={
            "skip_trace_id": skip_trace.id,
            "property_id": property.id,
            "property_address": property.address,
            "owner_name": skip_trace.owner_name,
            "owner_age": skip_trace.raw_response.get("age") if skip_trace.raw_response else None,
            "phone_count": len(skip_trace.phone_numbers or []),
            "email_count": len(skip_trace.emails or [])
        },
        context_summary=context.get_summary()
    )


@router.delete("/clear")
def clear_context(session_id: str = "default", db: Session = Depends(get_db)):
    """Clear conversation context"""
    context = get_context(session_id)
    context.clear()
    cleared = memory_graph_service.clear_session(db=db, session_id=session_id)
    db.commit()
    return {
        "success": True,
        "message": "Context cleared",
        "persistent_memory": cleared,
    }


class ContextEnrichRequest(BaseModel):
    """Enrich property with Zillow data using context"""
    property_ref: Optional[str] = None  # "this", "that", address, or ID
    session_id: str = "default"


@router.post("/enrich", response_model=ContextResponse)
@limiter.limit("10/minute")
async def enrich_property_with_zillow(
    request: Request,
    body: ContextEnrichRequest,
    db: Session = Depends(get_db)
):
    """
    Enrich property with comprehensive Zillow data.

    Uses context awareness to determine which property to enrich.

    Examples:
    - property_ref: null → Uses last property from context
    - property_ref: "this" → Uses last property
    - property_ref: "312 eisler" → Searches by address
    - property_ref: "2" → Uses property ID 2
    """
    # Resolve property reference
    property_id = resolve_property_reference(
        body.property_ref,
        body.session_id
    )

    if not property_id:
        # Try to search by address if provided
        if body.property_ref:
            query = body.property_ref.lower()
            property = (
                db.query(Property)
                .filter(Property.address.ilike(f"%{query}%"))
                .first()
            )
            if property:
                property_id = property.id

    if not property_id:
        raise HTTPException(
            status_code=400,
            detail="No property reference found. Please specify 'this property', an address, or property ID"
        )

    # Get property
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    # Build full address for Zillow API
    full_address = f"{property.address}, {property.city}, {property.state} {property.zip_code}"

    # Broadcast enrichment start via WebSocket
    manager = get_ws_manager()
    if manager:
        await manager.broadcast({
            "action": "enrichment_start",
            "property_id": property.id,
            "property_address": property.address
        })

    # Call Zillow API
    try:
        zillow_data = await zillow_enrichment_service.enrich_by_address(full_address)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enrich property from Zillow: {str(e)}"
        )

    # Check for existing enrichment
    existing_enrichment = (
        db.query(ZillowEnrichment)
        .filter(ZillowEnrichment.property_id == property.id)
        .first()
    )

    if existing_enrichment:
        # Update existing enrichment
        for key, value in zillow_data.items():
            if key != "raw_response":  # Handle raw_response separately
                setattr(existing_enrichment, key.replace("-", "_"), value)
        existing_enrichment.raw_response = zillow_data.get("raw_response")
        enrichment = existing_enrichment
    else:
        # Create new enrichment
        enrichment = ZillowEnrichment(
            property_id=property.id,
            zpid=zillow_data.get("zpid"),
            zestimate=zillow_data.get("zestimate"),
            zestimate_low=None,  # Calculate from percent
            zestimate_high=None,  # Calculate from percent
            rent_zestimate=zillow_data.get("rent_zestimate"),
            living_area=zillow_data.get("living_area"),
            lot_size=zillow_data.get("lot_area_value"),
            lot_area_units=zillow_data.get("lot_area_units"),
            year_built=zillow_data.get("year_built"),
            home_type=zillow_data.get("home_type"),
            home_status=zillow_data.get("home_status"),
            days_on_zillow=zillow_data.get("days_on_zillow"),
            page_view_count=zillow_data.get("page_view_count"),
            favorite_count=zillow_data.get("favorite_count"),
            property_tax_rate=zillow_data.get("property_tax_rate"),
            annual_tax_amount=zillow_data.get("annual_tax_amount"),
            hdp_url=zillow_data.get("hdp_url"),
            zillow_url=zillow_data.get("zillow_url"),
            photos=zillow_data.get("photos"),
            description=zillow_data.get("description"),
            schools=zillow_data.get("schools"),
            tax_history=zillow_data.get("tax_history"),
            price_history=zillow_data.get("price_history"),
            reso_facts=zillow_data.get("reso_facts"),
            raw_response=zillow_data.get("raw_response"),
        )
        db.add(enrichment)

    db.commit()
    db.refresh(enrichment)

    # Re-score property after enrichment
    from app.services.property_pipeline_service import calculate_property_score
    calculate_property_score(db, property)

    # Remember in context
    context = get_context(body.session_id)
    context.set_last_property(property.id, property.address)
    memory_graph_service.remember_property(
        db=db,
        session_id=body.session_id,
        property_id=property.id,
        address=property.address,
        city=property.city,
        state=property.state,
    )
    memory_graph_service.upsert_node(
        db=db,
        session_id=body.session_id,
        node_type="enrichment",
        node_key=str(property.id),
        summary=f"Zillow enrichment for property #{property.id}",
        payload={
            "zestimate": enrichment.zestimate,
            "rent_zestimate": enrichment.rent_zestimate,
            "zpid": enrichment.zpid,
            "photo_count": len(enrichment.photos) if enrichment.photos else 0,
        },
        importance=0.7,
    )
    memory_graph_service.upsert_edge(
        db=db,
        session_id=body.session_id,
        source=MemoryRef("enrichment", str(property.id)),
        target=MemoryRef("property", str(property.id)),
        relation="about_property",
        weight=0.7,
    )
    persist_context_to_graph(db=db, session_id=body.session_id)
    db.commit()

    # Build enrichment message
    message_parts = [f"Enriched {property.address} with Zillow data"]
    if enrichment.zpid:
        message_parts.append(f"ZPID: {enrichment.zpid}")
    if enrichment.zestimate:
        message_parts.append(f"Zestimate: ${enrichment.zestimate:,.0f}")
    enrichment_message = " (".join(message_parts)
    if len(message_parts) > 1:
        enrichment_message += ")"

    # Broadcast enrichment complete via WebSocket
    manager = get_ws_manager()
    if manager:
        await manager.broadcast({
            "action": "enrichment_complete",
            "property_id": property.id,
            "property_address": property.address
        })

    return ContextResponse(
        success=True,
        message=enrichment_message,
        data={
            "enrichment_id": enrichment.id,
            "property_id": property.id,
            "property_address": property.address,
            "zpid": enrichment.zpid,
            "zestimate": enrichment.zestimate,
            "rent_zestimate": enrichment.rent_zestimate,
            "living_area": enrichment.living_area,
            "lot_size": enrichment.lot_size,
            "year_built": enrichment.year_built,
            "home_type": enrichment.home_type,
            "photo_count": len(enrichment.photos) if enrichment.photos else 0,
            "zillow_url": enrichment.zillow_url,
        },
        context_summary=context.get_summary()
    )
