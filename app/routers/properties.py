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
from app.services.google_places import google_places_service

router = APIRouter(prefix="/properties", tags=["properties"])


@router.post("/", response_model=PropertyResponse, status_code=201)
def create_property(property: PropertyCreate, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == property.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    new_property = Property(**property.model_dump())
    db.add(new_property)
    db.commit()
    db.refresh(new_property)
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
def update_property(
    property_id: int, property: PropertyUpdate, db: Session = Depends(get_db)
):
    db_property = db.query(Property).filter(Property.id == property_id).first()
    if not db_property:
        raise HTTPException(status_code=404, detail="Property not found")

    update_data = property.model_dump(exclude_unset=True)

    if "agent_id" in update_data:
        agent = db.query(Agent).filter(Agent.id == update_data["agent_id"]).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

    for field, value in update_data.items():
        setattr(db_property, field, value)

    db.commit()
    db.refresh(db_property)
    return db_property


@router.delete("/{property_id}", status_code=204)
def delete_property(property_id: int, db: Session = Depends(get_db)):
    db_property = db.query(Property).filter(Property.id == property_id).first()
    if not db_property:
        raise HTTPException(status_code=404, detail="Property not found")

    db.delete(db_property)
    db.commit()
    return None
