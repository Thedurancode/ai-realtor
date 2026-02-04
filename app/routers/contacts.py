import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.property import Property
from app.models.contact import Contact, ContactRole
from app.schemas.contact import (
    ContactCreate,
    ContactUpdate,
    ContactResponse,
    ContactCreateFromVoice,
    ContactCreateFromVoiceResponse,
    ContactListVoiceResponse,
)

router = APIRouter(prefix="/contacts", tags=["contacts"])


# Role aliases for voice input
ROLE_ALIASES = {
    "lawyer": ContactRole.LAWYER,
    "attorney": ContactRole.LAWYER,
    "contractor": ContactRole.CONTRACTOR,
    "inspector": ContactRole.INSPECTOR,
    "home inspector": ContactRole.INSPECTOR,
    "appraiser": ContactRole.APPRAISER,
    "mortgage broker": ContactRole.MORTGAGE_BROKER,
    "mortgage": ContactRole.MORTGAGE_BROKER,
    "lender": ContactRole.LENDER,
    "bank": ContactRole.LENDER,
    "title company": ContactRole.TITLE_COMPANY,
    "title": ContactRole.TITLE_COMPANY,
    "buyer": ContactRole.BUYER,
    "seller": ContactRole.SELLER,
    "tenant": ContactRole.TENANT,
    "renter": ContactRole.TENANT,
    "landlord": ContactRole.LANDLORD,
    "property manager": ContactRole.PROPERTY_MANAGER,
    "pm": ContactRole.PROPERTY_MANAGER,
    "handyman": ContactRole.HANDYMAN,
    "plumber": ContactRole.PLUMBER,
    "electrician": ContactRole.ELECTRICIAN,
    "photographer": ContactRole.PHOTOGRAPHER,
    "stager": ContactRole.STAGER,
    "home stager": ContactRole.STAGER,
}


def parse_role(role_input: str) -> ContactRole:
    """Parse role from voice input, handling aliases."""
    role_lower = role_input.lower().strip()
    if role_lower in ROLE_ALIASES:
        return ROLE_ALIASES[role_lower]
    # Try direct enum match
    try:
        return ContactRole(role_lower)
    except ValueError:
        return ContactRole.OTHER


def parse_name(full_name: str) -> tuple[str, str | None, str | None]:
    """Parse full name into first and last name."""
    parts = full_name.strip().split()
    if len(parts) == 1:
        return full_name, parts[0], None
    elif len(parts) == 2:
        return full_name, parts[0], parts[1]
    else:
        # First name is first part, last name is everything else
        return full_name, parts[0], " ".join(parts[1:])


def format_phone_for_voice(phone: str) -> str:
    """Format phone number for voice readability."""
    digits = "".join(filter(str.isdigit, phone))
    if len(digits) == 10:
        return f"{digits[:3]}, {digits[3:6]}, {digits[6:]}"
    return phone


def format_role_for_voice(role: ContactRole) -> str:
    """Format role for voice output."""
    return role.value.replace("_", " ")


@router.post("/", response_model=ContactResponse, status_code=201)
def create_contact(contact: ContactCreate, db: Session = Depends(get_db)):
    """Create a contact for a property."""
    property = db.query(Property).filter(Property.id == contact.property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    full_name, first_name, last_name = parse_name(contact.name)

    new_contact = Contact(
        property_id=contact.property_id,
        name=full_name,
        first_name=first_name,
        last_name=last_name,
        role=contact.role,
        phone=contact.phone,
        email=contact.email,
        company=contact.company,
        notes=contact.notes,
    )
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)
    return new_contact


@router.post("/voice", response_model=ContactCreateFromVoiceResponse, status_code=201)
def create_contact_from_voice(
    request: ContactCreateFromVoice, db: Session = Depends(get_db)
):
    """
    Voice-optimized contact creation.
    Example: "add a lawyer to 141 throop, his name is Ed Duran, 201-335-5555"
    """
    # Find property by partial address
    query = request.address_query.lower()
    property = (
        db.query(Property)
        .filter(Property.address.ilike(f"%{query}%"))
        .first()
    )

    if not property:
        raise HTTPException(
            status_code=404,
            detail=f"No property found matching '{request.address_query}'. Please add the property first.",
        )

    # Parse role and name
    role = parse_role(request.role)
    full_name, first_name, last_name = parse_name(request.name)

    # Create contact
    new_contact = Contact(
        property_id=property.id,
        name=full_name,
        first_name=first_name,
        last_name=last_name,
        role=role,
        phone=request.phone,
        email=request.email,
        company=request.company,
        notes=request.notes,
    )
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)

    # Build voice confirmation
    role_text = format_role_for_voice(role)
    voice_confirmation = (
        f"Got it. I've added {full_name} as the {role_text} "
        f"for {property.address}, {property.city}."
    )
    if request.phone:
        voice_confirmation += f" Phone number: {format_phone_for_voice(request.phone)}."

    return ContactCreateFromVoiceResponse(
        contact=new_contact,
        voice_confirmation=voice_confirmation,
    )


@router.get("/property/{property_id}", response_model=ContactListVoiceResponse)
def list_contacts_for_property(property_id: int, db: Session = Depends(get_db)):
    """List all contacts for a property with voice summary."""
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    contacts = db.query(Contact).filter(Contact.property_id == property_id).all()

    if not contacts:
        voice_summary = f"No contacts found for {property.address}."
    else:
        # Group by role for summary
        role_counts = {}
        for c in contacts:
            role_text = format_role_for_voice(c.role)
            role_counts[role_text] = role_counts.get(role_text, 0) + 1

        role_parts = [f"{count} {role}{'s' if count > 1 else ''}" for role, count in role_counts.items()]
        voice_summary = (
            f"Found {len(contacts)} contact{'s' if len(contacts) > 1 else ''} "
            f"for {property.address}: {', '.join(role_parts)}. "
            "Would you like me to read the details?"
        )

    return ContactListVoiceResponse(
        contacts=contacts,
        voice_summary=voice_summary,
    )


@router.get("/property/{property_id}/role/{role}", response_model=ContactListVoiceResponse)
def get_contacts_by_role(property_id: int, role: str, db: Session = Depends(get_db)):
    """Get contacts for a property by role (voice-friendly)."""
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    parsed_role = parse_role(role)
    contacts = (
        db.query(Contact)
        .filter(Contact.property_id == property_id, Contact.role == parsed_role)
        .all()
    )

    role_text = format_role_for_voice(parsed_role)

    if not contacts:
        voice_summary = f"No {role_text} found for {property.address}."
    elif len(contacts) == 1:
        c = contacts[0]
        voice_summary = f"The {role_text} for {property.address} is {c.name}."
        if c.phone:
            voice_summary += f" Phone: {format_phone_for_voice(c.phone)}."
    else:
        names = [c.name for c in contacts]
        voice_summary = f"Found {len(contacts)} {role_text}s for {property.address}: {', '.join(names)}."

    return ContactListVoiceResponse(
        contacts=contacts,
        voice_summary=voice_summary,
    )


@router.get("/voice/search", response_model=ContactListVoiceResponse)
def search_contacts_voice(
    address_query: str,
    role: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Voice search for contacts.
    Example: "who is the lawyer for 141 throop"
    """
    query = address_query.lower()
    property = (
        db.query(Property)
        .filter(Property.address.ilike(f"%{query}%"))
        .first()
    )

    if not property:
        raise HTTPException(
            status_code=404,
            detail=f"No property found matching '{address_query}'.",
        )

    contacts_query = db.query(Contact).filter(Contact.property_id == property.id)

    if role:
        parsed_role = parse_role(role)
        contacts_query = contacts_query.filter(Contact.role == parsed_role)

    contacts = contacts_query.all()

    if role:
        role_text = format_role_for_voice(parse_role(role))
        if not contacts:
            voice_summary = f"No {role_text} found for {property.address}."
        elif len(contacts) == 1:
            c = contacts[0]
            voice_summary = f"The {role_text} for {property.address} is {c.name}."
            if c.phone:
                voice_summary += f" Phone: {format_phone_for_voice(c.phone)}."
        else:
            names = [c.name for c in contacts]
            voice_summary = f"Found {len(contacts)} {role_text}s: {', '.join(names)}."
    else:
        if not contacts:
            voice_summary = f"No contacts found for {property.address}."
        else:
            contact_parts = [f"{c.name}, {format_role_for_voice(c.role)}" for c in contacts[:5]]
            voice_summary = f"Contacts for {property.address}: {'. '.join(contact_parts)}."

    return ContactListVoiceResponse(
        contacts=contacts,
        voice_summary=voice_summary,
    )


@router.get("/{contact_id}", response_model=ContactResponse)
def get_contact(contact_id: int, db: Session = Depends(get_db)):
    """Get a contact by ID."""
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.patch("/{contact_id}", response_model=ContactResponse)
def update_contact(
    contact_id: int, contact: ContactUpdate, db: Session = Depends(get_db)
):
    """Update a contact."""
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not db_contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    update_data = contact.model_dump(exclude_unset=True)

    # Re-parse name if updated
    if "name" in update_data:
        full_name, first_name, last_name = parse_name(update_data["name"])
        update_data["name"] = full_name
        update_data["first_name"] = first_name
        update_data["last_name"] = last_name

    for field, value in update_data.items():
        setattr(db_contact, field, value)

    db.commit()
    db.refresh(db_contact)
    return db_contact


@router.delete("/{contact_id}", status_code=204)
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    """Delete a contact."""
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not db_contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    db.delete(db_contact)
    db.commit()
    return None
