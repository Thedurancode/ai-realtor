"""
Contact Lists API Router

Organize contacts into smart lists that auto-populate based on rules:
- Time-based: Last 2 days, This week, This month
- Property-based: Has property, No property
- Contact info: Has email, No phone
- Status: Uncontacted
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.contact_lists import ContactList, ListType, SmartListRule
from app.models.contact import Contact
from app.schemas.contact_lists import (
    ContactListCreate,
    ContactListUpdate,
    ContactListDetail,
    ContactListItem,
    ContactListVoiceSummary,
    SmartListCreate,
    QuickSmartListCreate,
    SMART_LIST_PRESETS,
    SmartListPreset
)
from app.models.agent import Agent


router = APIRouter(
    prefix="/contact-lists",
    tags=["Contact Lists"]
)


# ==========================================================================
# LIST CONTACT LISTS
# ==========================================================================

@router.get("", response_model=List[ContactListItem])
async def list_contact_lists(
    list_type: Optional[str] = Query(None, description="Filter by list type"),
    agent_id: Optional[int] = Query(None, description="Filter by agent"),
    db: Session = Depends(get_db)
):
    """
    List all contact lists

    Query Parameters:
    - list_type: Filter by type (smart, manual, imported, campaign)
    - agent_id: Filter by agent ID

    Returns list of contact lists with metadata
    """
    query = db.query(ContactList)

    if list_type:
        query = query.filter(ContactList.list_type == list_type)

    if agent_id:
        query = query.filter(ContactList.agent_id == agent_id)

    lists = query.order_by(ContactList.created_at.desc()).all()

    # Auto-refresh smart lists if needed
    for contact_list in lists:
        if contact_list.list_type == ListType.SMART and contact_list.auto_refresh:
            # Check if refresh is needed
            if (not contact_list.last_refreshed_at or
                (datetime.utcnow() - contact_list.last_refreshed_at).total_seconds() >
                contact_list.refresh_interval_hours * 3600):
                contact_list.refresh_count(db)

    return lists


@router.get("/presets", response_model=List[SmartListPreset])
async def get_smart_list_presets():
    """
    Get available smart list presets for quick creation

    Returns presets with name, display_name, description, and smart_rule
    """
    return SMART_LIST_PRESETS


# ==========================================================================
# CREATE CONTACT LISTS
# ==========================================================================

@router.post("", response_model=ContactListDetail, status_code=201)
async def create_contact_list(
    data: ContactListCreate,
    db: Session = Depends(get_db),
    agent_id: int = Query(None, description="Agent ID (from auth)")
):
    """
    Create a new contact list

    List Types:
    - manual: Manually curated list with specific contact IDs
    - smart: Auto-populated based on rules (time, property, contact info)
    - imported: Created from CSV import
    - campaign: Linked to a direct mail campaign

    Smart Rules:
    - last_24_hours: Contacts created in last 24 hours
    - last_2_days: Contacts created in last 48 hours
    - this_week: Contacts created this week (Monday onwards)
    - this_month: Contacts created this month
    - no_property: Contacts not linked to any property
    - has_property: Contacts linked to a property
    - no_phone: Contacts without phone number
    - has_email: Contacts with email address
    - uncontacted: Contacts that have never been contacted
    """
    if not agent_id:
        agent_id = 1

    # Validate agent exists
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Validate smart rule for smart lists
    if data.list_type == ListType.SMART and not data.smart_rule:
        raise HTTPException(
            status_code=400,
            detail="smart_rule is required when list_type=smart"
        )

    # Create contact list
    contact_list = ContactList(
        agent_id=agent_id,
        name=data.name,
        description=data.description,
        list_type=data.list_type,
        smart_rule=data.smart_rule,
        filters=data.filters,
        contact_ids=data.contact_ids,
        campaign_id=data.campaign_id,
        auto_refresh=data.auto_refresh,
        refresh_interval_hours=data.refresh_interval_hours,
        total_contacts=0,
        last_refreshed_at=datetime.utcnow() if data.list_type == ListType.SMART else None
    )

    db.add(contact_list)
    db.commit()
    db.refresh(contact_list)

    # Initial count refresh for smart lists
    if contact_list.list_type == ListType.SMART:
        contact_list.refresh_count(db)

    return contact_list


@router.post("/smart", response_model=ContactListDetail, status_code=201)
async def create_smart_list(
    data: SmartListCreate,
    db: Session = Depends(get_db),
    agent_id: int = Query(None, description="Agent ID (from auth)")
):
    """
    Create a smart list with auto-population

    Smart lists automatically update their contacts based on rules
    """
    if not agent_id:
        agent_id = 1

    # Validate agent exists
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Create smart list
    contact_list = ContactList(
        agent_id=agent_id,
        name=data.name,
        description=data.description,
        list_type=ListType.SMART,
        smart_rule=data.smart_rule,
        filters=data.filters,
        auto_refresh=data.auto_refresh,
        refresh_interval_hours=data.refresh_interval_hours,
        total_contacts=0,
        last_refreshed_at=datetime.utcnow()
    )

    db.add(contact_list)
    db.commit()
    db.refresh(contact_list)

    # Initial count refresh
    contact_list.refresh_count(db)

    return contact_list


@router.post("/quick", response_model=ContactListDetail, status_code=201)
async def create_quick_smart_list(
    data: QuickSmartListCreate,
    db: Session = Depends(get_db),
    agent_id: int = Query(None, description="Agent ID (from auth)")
):
    """
    Quick-create a smart list from preset

    Presets:
    - interested_this_week: Contacts added this week
    - new_leads_2days: Contacts added in last 2 days
    - new_leads_7days: Contacts added in last 7 days
    - this_month: Contacts added this month
    - uncontacted: Never contacted leads
    - no_phone: Missing phone numbers
    - has_email: Has email addresses
    - no_property: Not linked to any property

    Example:
    POST /contact-lists/quick?preset=interested_this_week
    POST /contact-lists/quick?preset=new_leads_2days&filters={"city":"Miami"}
    """
    if not agent_id:
        agent_id = 1

    # Find preset
    preset = next((p for p in SMART_LIST_PRESETS if p["name"] == data.preset), None)
    if not preset:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid preset. Available: {', '.join([p['name'] for p in SMART_LIST_PRESETS])}"
        )

    # Use custom name if provided, otherwise use suggested name
    name = data.custom_name if data.custom_name else preset["suggested_name"]

    # Create smart list
    contact_list = ContactList(
        agent_id=agent_id,
        name=name,
        description=preset["description"],
        list_type=ListType.SMART,
        smart_rule=preset["smart_rule"],
        filters=data.filters,
        auto_refresh=True,
        refresh_interval_hours=24,
        total_contacts=0,
        last_refreshed_at=datetime.utcnow()
    )

    db.add(contact_list)
    db.commit()
    db.refresh(contact_list)

    # Initial count refresh
    contact_list.refresh_count(db)

    return contact_list


# ==========================================================================
# GET CONTACT LIST DETAILS
# ==========================================================================

@router.get("/{list_id}", response_model=ContactListDetail)
async def get_contact_list(
    list_id: int,
    include_contacts: bool = Query(False, description="Include contacts in response"),
    limit: int = Query(100, description="Max contacts to return"),
    offset: int = Query(0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    Get contact list details

    Optionally include contacts with pagination
    """
    contact_list = db.query(ContactList).filter(ContactList.id == list_id).first()

    if not contact_list:
        raise HTTPException(status_code=404, detail="Contact list not found")

    # Refresh smart list if needed
    if contact_list.list_type == ListType.SMART and contact_list.auto_refresh:
        if (not contact_list.last_refreshed_at or
            (datetime.utcnow() - contact_list.last_refreshed_at).total_seconds() >
            contact_list.refresh_interval_hours * 3600):
            contact_list.refresh_count(db)

    result = ContactListDetail.from_orm(contact_list)

    # Include contacts if requested
    if include_contacts:
        query = contact_list.get_contacts_query(db)
        contacts = query.offset(offset).limit(limit).all()

        result.contacts = [
            {
                "id": c.id,
                "name": c.name,
                "email": c.email,
                "phone": c.phone,
                "address": f"{c.address}, {c.city}, {c.state} {c.zip_code}",
                "property_id": c.property_id,
                "created_at": c.created_at.isoformat()
            }
            for c in contacts
        ]

    return result


@router.get("/{list_id}/voice", response_model=ContactListVoiceSummary)
async def get_contact_list_voice_summary(
    list_id: int,
    db: Session = Depends(get_db)
):
    """
    Get voice-friendly summary for TTS
    """
    contact_list = db.query(ContactList).filter(ContactList.id == list_id).first()

    if not contact_list:
        raise HTTPException(status_code=404, detail="Contact list not found")

    # Refresh if needed
    if contact_list.list_type == ListType.SMART and contact_list.auto_refresh:
        contact_list.refresh_count(db)

    # Build voice summary
    type_voice = {
        ListType.SMART: "Smart list",
        ListType.MANUAL: "Manual list",
        ListType.IMPORTED: "Imported list",
        ListType.CAMPAIGN: "Campaign list"
    }.get(contact_list.list_type, "List")

    if contact_list.list_type == ListType.SMART:
        rule_voice = contact_list.smart_rule.replace("_", " ")
        voice_summary = f"{type_voice} '{contact_list.name}' has {contact_list.total_contacts} contacts based on {rule_voice}."
    else:
        voice_summary = f"{type_voice} '{contact_list.name}' has {contact_list.total_contacts} contacts."

    last_refreshed = contact_list.last_refreshed_at.strftime("%I:%M %p") if contact_list.last_refreshed_at else None

    return ContactListVoiceSummary(
        id=contact_list.id,
        name=contact_list.name,
        list_type=contact_list.list_type,
        total_contacts=contact_list.total_contacts,
        voice_summary=voice_summary,
        last_refreshed=last_refreshed
    )


# ==========================================================================
# UPDATE CONTACT LISTS
# ==========================================================================

@router.put("/{list_id}", response_model=ContactListDetail)
async def update_contact_list(
    list_id: int,
    data: ContactListUpdate,
    db: Session = Depends(get_db)
):
    """
    Update contact list

    For smart lists, updating smart_rule or filters will refresh the list
    """
    contact_list = db.query(ContactList).filter(ContactList.id == list_id).first()

    if not contact_list:
        raise HTTPException(status_code=404, detail="Contact list not found")

    # Update fields
    if data.name is not None:
        contact_list.name = data.name
    if data.description is not None:
        contact_list.description = data.description
    if data.smart_rule is not None:
        contact_list.smart_rule = data.smart_rule
    if data.filters is not None:
        contact_list.filters = data.filters
    if data.contact_ids is not None:
        contact_list.contact_ids = data.contact_ids
    if data.auto_refresh is not None:
        contact_list.auto_refresh = data.auto_refresh
    if data.refresh_interval_hours is not None:
        contact_list.refresh_interval_hours = data.refresh_interval_hours

    # Refresh smart list if rule or filters changed
    if contact_list.list_type == ListType.SMART and (data.smart_rule or data.filters):
        contact_list.refresh_count(db)

    db.commit()
    db.refresh(contact_list)

    return contact_list


# ==========================================================================
# REFRESH SMART LIST
# ==========================================================================

@router.post("/{list_id}/refresh", response_model=ContactListDetail)
async def refresh_smart_list(
    list_id: int,
    db: Session = Depends(get_db)
):
    """
    Manually refresh a smart list to update contacts

    Also updates the last_refreshed_at timestamp
    """
    contact_list = db.query(ContactList).filter(ContactList.id == list_id).first()

    if not contact_list:
        raise HTTPException(status_code=404, detail="Contact list not found")

    if contact_list.list_type != ListType.SMART:
        raise HTTPException(
            status_code=400,
            detail="Only smart lists can be refreshed"
        )

    contact_list.refresh_count(db)
    db.refresh(contact_list)

    return contact_list


# ==========================================================================
# DELETE CONTACT LIST
# ==========================================================================

@router.delete("/{list_id}")
async def delete_contact_list(
    list_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a contact list

    This only deletes the list, not the contacts themselves
    """
    contact_list = db.query(ContactList).filter(ContactList.id == list_id).first()

    if not contact_list:
        raise HTTPException(status_code=404, detail="Contact list not found")

    db.delete(contact_list)
    db.commit()

    return {
        "message": f"Contact list '{contact_list.name}' deleted successfully",
        "id": list_id
    }


# ==========================================================================
# ADD/REMOVE CONTACTS FROM MANUAL LIST
# ==========================================================================

@router.post("/{list_id}/contacts", response_model=ContactListDetail)
async def add_contacts_to_list(
    list_id: int,
    contact_ids: List[int],
    db: Session = Depends(get_db)
):
    """
    Add contacts to a manual list

    Only works for manual lists, not smart lists
    """
    contact_list = db.query(ContactList).filter(ContactList.id == list_id).first()

    if not contact_list:
        raise HTTPException(status_code=404, detail="Contact list not found")

    if contact_list.list_type != ListType.MANUAL:
        raise HTTPException(
            status_code=400,
            detail="Can only add contacts to manual lists"
        )

    # Add contact IDs
    if not contact_list.contact_ids:
        contact_list.contact_ids = []

    # Add only new contacts (avoid duplicates)
    for contact_id in contact_ids:
        if contact_id not in contact_list.contact_ids:
            contact_list.contact_ids.append(contact_id)

    contact_list.total_contacts = len(contact_list.contact_ids)
    db.commit()
    db.refresh(contact_list)

    return contact_list


@router.delete("/{list_id}/contacts", response_model=ContactListDetail)
async def remove_contacts_from_list(
    list_id: int,
    contact_ids: List[int],
    db: Session = Depends(get_db)
):
    """
    Remove contacts from a manual list
    """
    contact_list = db.query(ContactList).filter(ContactList.id == list_id).first()

    if not contact_list:
        raise HTTPException(status_code=404, detail="Contact list not found")

    if contact_list.list_type != ListType.MANUAL:
        raise HTTPException(
            status_code=400,
            detail="Can only remove contacts from manual lists"
        )

    # Remove contact IDs
    if contact_list.contact_ids:
        for contact_id in contact_ids:
            if contact_id in contact_list.contact_ids:
                contact_list.contact_ids.remove(contact_id)

    contact_list.total_contacts = len(contact_list.contact_ids) if contact_list.contact_ids else 0
    db.commit()
    db.refresh(contact_list)

    return contact_list


# ==========================================================================
# CAMPAIGN CREATION FROM LIST
# ==========================================================================

@router.post("/{list_id}/create-campaign", response_model=dict)
async def create_campaign_from_list(
    list_id: int,
    template: str = Query("interested_in_selling", description="Template to use"),
    campaign_name: Optional[str] = Query(None, description="Campaign name"),
    send_immediately: bool = Query(False, description="Send immediately"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Create a direct mail campaign from a contact list

    Uses all contacts in the list as campaign targets
    """
    contact_list = db.query(ContactList).filter(ContactList.id == list_id).first()

    if not contact_list:
        raise HTTPException(status_code=404, detail="Contact list not found")

    # Get contact IDs from list
    if contact_list.list_type == ListType.SMART:
        # For smart lists, get IDs dynamically
        query = contact_list.get_contacts_query(db)
        contacts = query.all()
        target_contact_ids = [c.id for c in contacts]
    else:
        # For manual lists, use stored IDs
        target_contact_ids = contact_list.contact_ids or []

    if not target_contact_ids:
        raise HTTPException(
            status_code=400,
            detail="No contacts in list to create campaign"
        )

    # Import here to avoid circular import
    from app.routers.direct_mail import execute_campaign
    from app.models.direct_mail import DirectMailCampaign, MailType

    # Generate campaign name
    if not campaign_name:
        campaign_name = f"{contact_list.name} - {datetime.now().strftime('%b %d')}"

    # Create campaign
    campaign = DirectMailCampaign(
        agent_id=contact_list.agent_id,
        name=campaign_name,
        description=f"Campaign created from contact list '{contact_list.name}' with {len(target_contact_ids)} contacts",
        campaign_type=template,
        mail_type=MailType.POSTCARD,
        template_id=None,
        target_contact_ids=target_contact_ids,
        filters={"source_list_id": contact_list.id},
        color=True,
        double_sided=True,
        send_immediately=send_immediately,
        total_recipients=len(target_contact_ids),
        sent_count=0,
        delivered_count=0,
        failed_count=0,
        total_cost=0.0,
        status="draft"
    )

    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    # Send immediately if requested
    if send_immediately and background_tasks:
        background_tasks.add_task(execute_campaign, campaign.id)

    return {
        "message": f"Campaign created from list '{contact_list.name}' with {len(target_contact_ids)} contacts",
        "campaign_id": campaign.id,
        "campaign_name": campaign.name,
        "contact_count": len(target_contact_ids),
        "send_immediately": send_immediately
    }
