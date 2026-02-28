import re
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.property import Property
from app.models.contact import Contact, ContactRole
from app.models.contract import Contract, ContractStatus
from app.services.notification_service import notification_service
from app.services.contract_smart_send import get_required_roles, find_contacts_for_roles
from app.services.conversation_context import get_context, persist_context_to_graph
from app.services.memory_graph import memory_graph_service
from app.schemas.contact import (
    ContactCreate,
    ContactUpdate,
    ContactResponse,
    ContactCreateFromVoice,
    ContactCreateFromVoiceResponse,
    ContactListVoiceResponse,
)
from app.utils.websocket import get_ws_manager

router = APIRouter(prefix="/contacts", tags=["contacts"])
from app.utils.websocket import get_ws_manager




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
from app.utils.websocket import get_ws_manager
    if role_lower in ROLE_ALIASES:
        return ROLE_ALIASES[role_lower]
    # Try direct enum match
    try:
        return ContactRole(role_lower)
from app.utils.websocket import get_ws_manager
    except ValueError:
        return ContactRole.OTHER


def parse_name(full_name: str) -> tuple[str, str | None, str | None]:
    """Parse full name into first and last name."""
    parts = full_name.strip().split()
from app.utils.websocket import get_ws_manager
    if len(parts) == 1:
        return full_name, parts[0], None
    elif len(parts) == 2:
        return full_name, parts[0], parts[1]
    else:
        # First name is first part, last name is everything else
        return full_name, parts[0], " ".join(parts[1:])
from app.utils.websocket import get_ws_manager


def format_phone_for_voice(phone: str) -> str:
    """Format phone number for voice readability."""
    digits = "".join(filter(str.isdigit, phone))
from app.utils.websocket import get_ws_manager
    if len(digits) == 10:
        return f"{digits[:3]}, {digits[3:6]}, {digits[6:]}"
    return phone


def format_role_for_voice(role: ContactRole) -> str:
    """Format role for voice output."""
    return role.value.replace("_", " ")
from app.utils.websocket import get_ws_manager


@router.post("/", response_model=ContactResponse, status_code=201)
from app.utils.websocket import get_ws_manager
async def create_contact(contact: ContactCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Create a contact for a property."""
    property = db.query(Property).filter(Property.id == contact.property_id).first()
from app.utils.websocket import get_ws_manager
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")
from app.utils.websocket import get_ws_manager

    full_name, first_name, last_name = parse_name(contact.name)
from app.utils.websocket import get_ws_manager

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
from app.utils.websocket import get_ws_manager
    db.add(new_contact)
from app.utils.websocket import get_ws_manager
    db.commit()
from app.utils.websocket import get_ws_manager
    db.refresh(new_contact)
from app.utils.websocket import get_ws_manager

    # Send notification for new leads (buyers/sellers)
from app.utils.websocket import get_ws_manager
    if contact.role in [ContactRole.BUYER, ContactRole.SELLER]:
        manager = get_ws_manager()
from app.utils.websocket import get_ws_manager
        await notification_service.notify_new_lead(
            db=db,
            manager=manager,
            contact_id=new_contact.id,
            contact_name=new_contact.name,
            contact_email=new_contact.email,
            contact_phone=new_contact.phone,
            property_address=property.address,
            property_id=property.id,
            lead_source="Manual Entry"
        )
from app.utils.websocket import get_ws_manager

    from app.services.property_recap_service import regenerate_recap_background
    background_tasks.add_task(regenerate_recap_background, property.id, "contact_added")
from app.utils.websocket import get_ws_manager

    return new_contact


@router.post("/voice", response_model=ContactCreateFromVoiceResponse, status_code=201)
from app.utils.websocket import get_ws_manager
async def create_contact_from_voice(
    request: ContactCreateFromVoice, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
):
    """
    Voice-optimized contact creation.
    Example: "add a lawyer to 141 throop, his name is Ed Duran, 201-335-5555"
    """
    # Find property by partial address
    query = request.address_query.lower()
from app.utils.websocket import get_ws_manager
    property = (
        db.query(Property)
from app.utils.websocket import get_ws_manager
        .filter(Property.address.ilike(f"%{query}%"))
from app.utils.websocket import get_ws_manager
        .first()
from app.utils.websocket import get_ws_manager
    )
from app.utils.websocket import get_ws_manager

    if not property:
        raise HTTPException(
            status_code=404,
            detail=f"No property found matching '{request.address_query}'. Please add the property first.",
        )
from app.utils.websocket import get_ws_manager

    # Parse role and name
    role = parse_role(request.role)
from app.utils.websocket import get_ws_manager
    full_name, first_name, last_name = parse_name(request.name)
from app.utils.websocket import get_ws_manager

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
from app.utils.websocket import get_ws_manager
    db.add(new_contact)
from app.utils.websocket import get_ws_manager
    db.commit()
from app.utils.websocket import get_ws_manager
    db.refresh(new_contact)
from app.utils.websocket import get_ws_manager

    # Persist voice memory for people/property context.
    context = get_context(request.session_id)
from app.utils.websocket import get_ws_manager
    context.set_last_property(property.id, property.address)
from app.utils.websocket import get_ws_manager
    context.set_last_contact(new_contact.id, new_contact.name)
from app.utils.websocket import get_ws_manager
    memory_graph_service.remember_property(
        db=db,
        session_id=request.session_id,
        property_id=property.id,
        address=property.address,
        city=property.city,
        state=property.state,
    )
from app.utils.websocket import get_ws_manager
    memory_graph_service.remember_contact(
        db=db,
        session_id=request.session_id,
        contact_id=new_contact.id,
        name=new_contact.name,
        role=new_contact.role.value if new_contact.role else None,
        property_id=property.id,
    )
from app.utils.websocket import get_ws_manager
    persist_context_to_graph(db=db, session_id=request.session_id)
from app.utils.websocket import get_ws_manager
    db.commit()
from app.utils.websocket import get_ws_manager

    # Build voice confirmation
    role_text = format_role_for_voice(role)
from app.utils.websocket import get_ws_manager
    voice_confirmation = (
        f"Got it. I've added {full_name} as the {role_text} "
        f"for {property.address}, {property.city}."
    )
from app.utils.websocket import get_ws_manager
    if request.phone:
        voice_confirmation += f" Phone number: {format_phone_for_voice(request.phone)}."

    from app.services.property_recap_service import regenerate_recap_background
    background_tasks.add_task(regenerate_recap_background, property.id, "contact_added")
from app.utils.websocket import get_ws_manager

    return ContactCreateFromVoiceResponse(
        contact=new_contact,
        voice_confirmation=voice_confirmation,
    )
from app.utils.websocket import get_ws_manager


@router.get("/property/{property_id}", response_model=ContactListVoiceResponse)
from app.utils.websocket import get_ws_manager
def list_contacts_for_property(property_id: int, db: Session = Depends(get_db)):
    """List all contacts for a property with voice summary."""
    property = db.query(Property).filter(Property.id == property_id).first()
from app.utils.websocket import get_ws_manager
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")
from app.utils.websocket import get_ws_manager

    contacts = db.query(Contact).filter(Contact.property_id == property_id).all()
from app.utils.websocket import get_ws_manager

    if not contacts:
        voice_summary = f"No contacts found for {property.address}."
    else:
        # Group by role for summary
        role_counts = {}
        for c in contacts:
            role_text = format_role_for_voice(c.role)
from app.utils.websocket import get_ws_manager
            role_counts[role_text] = role_counts.get(role_text, 0) + 1

        role_parts = [f"{count} {role}{'s' if count > 1 else ''}" for role, count in role_counts.items()]
        voice_summary = (
            f"Found {len(contacts)} contact{'s' if len(contacts) > 1 else ''} "
            f"for {property.address}: {', '.join(role_parts)}. "
            "Would you like me to read the details?"
        )
from app.utils.websocket import get_ws_manager

    return ContactListVoiceResponse(
        contacts=contacts,
        voice_summary=voice_summary,
    )
from app.utils.websocket import get_ws_manager


@router.get("/property/{property_id}/role/{role}", response_model=ContactListVoiceResponse)
from app.utils.websocket import get_ws_manager
def get_contacts_by_role(property_id: int, role: str, db: Session = Depends(get_db)):
    """Get contacts for a property by role (voice-friendly)."""
    property = db.query(Property).filter(Property.id == property_id).first()
from app.utils.websocket import get_ws_manager
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")
from app.utils.websocket import get_ws_manager

    parsed_role = parse_role(role)
from app.utils.websocket import get_ws_manager
    contacts = (
        db.query(Contact)
from app.utils.websocket import get_ws_manager
        .filter(Contact.property_id == property_id, Contact.role == parsed_role)
from app.utils.websocket import get_ws_manager
        .all()
from app.utils.websocket import get_ws_manager
    )
from app.utils.websocket import get_ws_manager

    role_text = format_role_for_voice(parsed_role)
from app.utils.websocket import get_ws_manager

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
from app.utils.websocket import get_ws_manager


@router.get("/voice/search", response_model=ContactListVoiceResponse)
from app.utils.websocket import get_ws_manager
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
from app.utils.websocket import get_ws_manager
    property = (
        db.query(Property)
from app.utils.websocket import get_ws_manager
        .filter(Property.address.ilike(f"%{query}%"))
from app.utils.websocket import get_ws_manager
        .first()
from app.utils.websocket import get_ws_manager
    )
from app.utils.websocket import get_ws_manager

    if not property:
        raise HTTPException(
            status_code=404,
            detail=f"No property found matching '{address_query}'.",
        )
from app.utils.websocket import get_ws_manager

    contacts_query = db.query(Contact).filter(Contact.property_id == property.id)
from app.utils.websocket import get_ws_manager

    if role:
        parsed_role = parse_role(role)
from app.utils.websocket import get_ws_manager
        contacts_query = contacts_query.filter(Contact.role == parsed_role)
from app.utils.websocket import get_ws_manager

    contacts = contacts_query.all()
from app.utils.websocket import get_ws_manager

    if role:
        role_text = format_role_for_voice(parse_role(role))
from app.utils.websocket import get_ws_manager
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
from app.utils.websocket import get_ws_manager


@router.get("/{contact_id}", response_model=ContactResponse)
from app.utils.websocket import get_ws_manager
def get_contact(contact_id: int, db: Session = Depends(get_db)):
    """Get a contact by ID."""
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
from app.utils.websocket import get_ws_manager
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
from app.utils.websocket import get_ws_manager
    return contact


@router.patch("/{contact_id}", response_model=ContactResponse)
from app.utils.websocket import get_ws_manager
def update_contact(
    contact_id: int, contact: ContactUpdate, db: Session = Depends(get_db)
from app.utils.websocket import get_ws_manager
):
    """Update a contact."""
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
from app.utils.websocket import get_ws_manager
    if not db_contact:
        raise HTTPException(status_code=404, detail="Contact not found")
from app.utils.websocket import get_ws_manager

    update_data = contact.model_dump(exclude_unset=True)
from app.utils.websocket import get_ws_manager

    # Re-parse name if updated
    if "name" in update_data:
        full_name, first_name, last_name = parse_name(update_data["name"])
from app.utils.websocket import get_ws_manager
        update_data["name"] = full_name
        update_data["first_name"] = first_name
        update_data["last_name"] = last_name

    for field, value in update_data.items():
        setattr(db_contact, field, value)
from app.utils.websocket import get_ws_manager

    db.commit()
from app.utils.websocket import get_ws_manager
    db.refresh(db_contact)
from app.utils.websocket import get_ws_manager
    return db_contact


@router.post("/{contact_id}/send-pending-contracts", response_model=dict)
from app.utils.websocket import get_ws_manager
def send_pending_contracts_to_contact(
    contact_id: int,
    db: Session = Depends(get_db),
):
    """
    Find all draft contracts on the contact's property that need this contact's role
    and return them for sending.

    Example: Contact is a lawyer → finds contracts needing a lawyer signature.
    """
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
from app.utils.websocket import get_ws_manager
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
from app.utils.websocket import get_ws_manager

    property = db.query(Property).filter(Property.id == contact.property_id).first()
from app.utils.websocket import get_ws_manager
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")
from app.utils.websocket import get_ws_manager

    # Find all draft contracts on this property
    draft_contracts = db.query(Contract).filter(
        Contract.property_id == contact.property_id,
        Contract.status == ContractStatus.DRAFT,
    ).all()
from app.utils.websocket import get_ws_manager

    if not draft_contracts:
        role_text = contact.role.value.replace("_", " ")
from app.utils.websocket import get_ws_manager
        return {
            "contact_id": contact.id,
            "contact_name": contact.name,
            "property_address": property.address,
            "matched_contracts": [],
            "sent_count": 0,
            "voice_summary": f"No draft contracts found for {property.address} to send to {contact.name}.",
        }

    # Find contracts that need this contact's role
    contact_role_str = contact.role.value  # e.g., "lawyer", "buyer"
    matched = []

    for contract in draft_contracts:
        roles = get_required_roles(contract, db)
from app.utils.websocket import get_ws_manager
        if not roles:
            continue
        # Check if this contact's role is needed
        role_lower = [r.lower() for r in roles]
        if contact_role_str.lower() in role_lower:
            # Check if all required signers are available
            found_contacts, missing_roles = find_contacts_for_roles(
                db, contact.property_id, roles
            )
from app.utils.websocket import get_ws_manager
            matched.append({
                "contract_id": contract.id,
                "contract_name": contract.name,
                "required_roles": roles,
                "found_signers": [
                    {"name": f["contact"].name, "role": f["role_str"], "email": f["contact"].email}
                    for f in found_contacts
                ],
                "missing_roles": missing_roles,
                "ready_to_send": len(missing_roles) == 0,
            })
from app.utils.websocket import get_ws_manager

    role_text = contact.role.value.replace("_", " ")
from app.utils.websocket import get_ws_manager
    if not matched:
        voice_summary = (
            f"No contracts on {property.address} require a {role_text}'s signature."
        )
from app.utils.websocket import get_ws_manager
    else:
        ready = [m for m in matched if m["ready_to_send"]]
        not_ready = [m for m in matched if not m["ready_to_send"]]
        parts = []
        if ready:
            names = ", ".join(m["contract_name"] for m in ready)
from app.utils.websocket import get_ws_manager
            parts.append(f"{len(ready)} contract{'s' if len(ready) != 1 else ''} ready to send: {names}")
from app.utils.websocket import get_ws_manager
        if not_ready:
            for m in not_ready:
                parts.append(
                    f"{m['contract_name']} needs {', '.join(m['missing_roles'])} before sending"
                )
from app.utils.websocket import get_ws_manager
        voice_summary = (
            f"Found {len(matched)} contract{'s' if len(matched) != 1 else ''} "
            f"needing {contact.name}'s signature on {property.address}. "
            + ". ".join(parts) + "."
        )
from app.utils.websocket import get_ws_manager

    return {
        "contact_id": contact.id,
        "contact_name": contact.name,
        "contact_role": contact_role_str,
        "property_id": property.id,
        "property_address": property.address,
        "matched_contracts": matched,
        "sent_count": len([m for m in matched if m["ready_to_send"]]),
        "voice_summary": voice_summary,
    }


@router.delete("/{contact_id}", status_code=204)
from app.utils.websocket import get_ws_manager
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    """Delete a contact."""
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
from app.utils.websocket import get_ws_manager
    if not db_contact:
        raise HTTPException(status_code=404, detail="Contact not found")
from app.utils.websocket import get_ws_manager

    db.delete(db_contact)
from app.utils.websocket import get_ws_manager
    db.commit()
from app.utils.websocket import get_ws_manager
    return None
