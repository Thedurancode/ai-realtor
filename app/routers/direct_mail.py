"""
Direct Mail API Router

Endpoints for sending postcards, letters, and checks via Lob.com
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import csv
import io

from app.database import get_db
from app.models.direct_mail import (
    DirectMail,
    DirectMailTemplate,
    DirectMailCampaign,
    MailType,
    MailStatus
)
from app.models import Contact
from app.schemas.direct_mail import (
    PostcardCreate,
    LetterCreate,
    CheckCreate,
    BulkPostcardCreate,
    DirectMailResponse,
    DirectMailVoiceSummary,
    DirectMailTemplateCreate,
    DirectMailTemplateResponse,
    DirectMailCampaignCreate,
    DirectMailCampaignResponse,
    AddressVerificationRequest,
    AddressVerificationResponse
)
from app.services.lob_service import LobClient, DirectMailService

router = APIRouter(prefix="/direct-mail", tags=["Direct Mail"])


# ==========================================================================
# POSTCARDS
# ==========================================================================

@router.post("/postcards", response_model=DirectMailResponse)
async def send_postcard(
    data: PostcardCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    agent_id: int = Query(None, description="Agent ID (from auth)")
):
    """
    Send a postcard via Lob.com

    - **to_address**: Recipient postal address
    - **front_html**: HTML for front of postcard (supports {{variables}})
    - **back_html**: HTML for back of postcard (optional)
    - **size**: Postcard size (4x6, 6x9, 6x11)
    - **merge_variables**: Variables to merge into HTML templates
    - **send_after**: Schedule for future sending (optional)
    """
    # Default to agent_id=1 if not provided (for development)
    if not agent_id:
        agent_id = 1

    # Get agent's return address
    from app.models import Agent
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Use provided from_address or agent's default
    if not data.from_address:
        data.from_address = {
            "name": agent.full_name or "Real Estate Agent",
            "company": agent.brokerage or "",
            "address_line1": agent.office_address or "123 Main St",
            "address_city": agent.office_city or "Anytown",
            "address_state": agent.office_state or "CA",
            "address_zip": agent.office_zip or "90210",
            "address_country": "US"
        }

    # Verify addresses first
    lob_client = LobClient()
    try:
        verified_to = await lob_client.verify_address(data.to_address.dict())
        verified_from = await lob_client.verify_address(data.from_address.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Address verification failed: {str(e)}")
    finally:
        await lob_client.close()

    # Create mailpiece record
    mailpiece = DirectMail(
        agent_id=agent_id,
        property_id=data.property_id,
        contact_id=data.contact_id,
        mail_type=MailType.POSTCARD,
        mail_status=MailStatus.PROCESSING,
        to_address=verified_to,
        from_address=verified_from,
        front_html=data.front_html,
        back_html=data.back_html,
        postcard_size=data.postcard_size,
        merge_variables=data.merge_variables,
        send_after=data.send_after,
        template_name=data.template_name,
        campaign_name=data.campaign_name,
        campaign_type=data.campaign_type,
        description=data.description
    )

    db.add(mailpiece)
    db.commit()
    db.refresh(mailpiece)

    # Send to Lob in background
    background_tasks.add_task(
        send_postcard_to_lob,
        mailpiece.id,
        data.dict(),
        agent_id
    )

    return mailpiece


@router.get("/postcards", response_model=List[DirectMailResponse])
async def list_postcards(
    status: Optional[MailStatus] = None,
    property_id: Optional[int] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List all postcards sent by agent"""
    query = db.query(DirectMail).filter(DirectMail.mail_type == MailType.POSTCARD)

    if status:
        query = query.filter(DirectMail.mail_status == status)
    if property_id:
        query = query.filter(DirectMail.property_id == property_id)

    return query.order_by(DirectMail.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/postcards/{mailpiece_id}", response_model=DirectMailResponse)
async def get_postcard(mailpiece_id: int, db: Session = Depends(get_db)):
    """Get postcard details and sync status from Lob"""
    mailpiece = db.query(DirectMail).filter(
        DirectMail.id == mailpiece_id,
        DirectMail.mail_type == MailType.POSTCARD
    ).first()

    if not mailpiece:
        raise HTTPException(status_code=404, detail="Postcard not found")

    # Sync status from Lob
    if mailpiece.lob_mailpiece_id:
        await sync_mailpiece_status(mailpiece, db)

    return mailpiece


@router.post("/postcards/{mailpiece_id}/cancel")
async def cancel_postcard(mailpiece_id: int, db: Session = Depends(get_db)):
    """Cancel a postcard (before it's processed for mailing)"""
    mailpiece = db.query(DirectMail).filter(
        DirectMail.id == mailpiece_id,
        DirectMail.mail_type == MailType.POSTCARD
    ).first()

    if not mailpiece:
        raise HTTPException(status_code=404, detail="Postcard not found")

    if mailpiece.mail_status not in [MailStatus.DRAFT, MailStatus.SCHEDULED]:
        raise HTTPException(
            status_code=400,
            detail="Can only cancel postcards in draft or scheduled status"
        )

    # Cancel via Lob
    if mailpiece.lob_mailpiece_id:
        lob_client = LobClient()
        try:
            await lob_client.cancel_postcard(mailpiece.lob_mailpiece_id)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Cancellation failed: {str(e)}")
        finally:
            await lob_client.close()

    mailpiece.mail_status = MailStatus.CANCELLED
    db.commit()

    return {"message": "Postcard cancelled successfully"}


# ==========================================================================
# LETTERS
# ==========================================================================

@router.post("/letters", response_model=DirectMailResponse)
async def send_letter(
    data: LetterCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    agent_id: int = Query(None, description="Agent ID (from auth)")
):
    """Send a letter via Lob.com"""
    if not agent_id:
        agent_id = 1

    # Get agent info
    from app.models import Agent
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Use provided from_address or agent's default
    if not data.from_address:
        data.from_address = {
            "name": agent.full_name or "Real Estate Agent",
            "company": agent.brokerage or "",
            "address_line1": agent.office_address or "123 Main St",
            "address_city": agent.office_city or "Anytown",
            "address_state": agent.office_state or "CA",
            "address_zip": agent.office_zip or "90210",
            "address_country": "US"
        }

    # Verify addresses
    lob_client = LobClient()
    try:
        verified_to = await lob_client.verify_address(data.to_address.dict())
        verified_from = await lob_client.verify_address(data.from_address.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Address verification failed: {str(e)}")
    finally:
        await lob_client.close()

    # Create mailpiece record
    mailpiece = DirectMail(
        agent_id=agent_id,
        property_id=data.property_id,
        contact_id=data.contact_id,
        mail_type=MailType.LETTER,
        mail_status=MailStatus.PROCESSING,
        to_address=verified_to,
        from_address=verified_from,
        file_url=data.file_url,
        letter_size=data.letter_size,
        color=data.color,
        double_sided=data.double_sided,
        certified_mail=data.certified_mail,
        return_envelope=data.return_envelope,
        send_after=data.send_after,
        campaign_name=data.campaign_name,
        campaign_type=data.campaign_type
    )

    db.add(mailpiece)
    db.commit()
    db.refresh(mailpiece)

    # Send to Lob in background
    background_tasks.add_task(
        send_letter_to_lob,
        mailpiece.id,
        data.dict(),
        agent_id
    )

    return mailpiece


# ==========================================================================
# BULK CAMPAIGNS
# ==========================================================================

@router.post("/campaigns", response_model=DirectMailCampaignResponse)
async def create_campaign(
    data: DirectMailCampaignCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    agent_id: int = Query(None, description="Agent ID (from auth)")
):
    """
    Create a bulk direct mail campaign

    - **target_property_ids**: Specific properties to target
    - **target_contact_ids**: Specific contacts to target
    - **filters**: Dynamic filters (city, price range, property_type, etc.)
    - **template_id**: Template to use
    - **send_immediately**: Send immediately or schedule
    - **scheduled_for**: When to send (if not immediate)
    """
    if not agent_id:
        agent_id = 1

    # Build recipient list
    recipients = []
    if data.target_property_ids:
        # Add property owners
        from app.models import Property
        properties = db.query(Property).filter(
            Property.id.in_(data.target_property_ids)
        ).all()
        for prop in properties:
            # TODO: Get property owner contacts
            pass

    if data.target_contact_ids:
        recipients.extend(data.target_contact_ids)

    # Create campaign
    campaign = DirectMailCampaign(
        agent_id=agent_id,
        template_id=data.template_id,
        name=data.name,
        description=data.description,
        campaign_type=data.campaign_type,
        mail_type=data.mail_type,
        postcard_size=data.postcard_size,
        color=data.color,
        double_sided=data.double_sided,
        target_property_ids=data.target_property_ids,
        target_contact_ids=data.target_contact_ids,
        filters=data.filters,
        total_recipients=len(recipients),
        scheduled_for=data.scheduled_for
    )

    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    # Send in background if immediate
    if data.send_immediately:
        background_tasks.add_task(execute_campaign, campaign.id)

    return campaign


@router.get("/campaigns", response_model=List[DirectMailCampaignResponse])
async def list_campaigns(
    status: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List all campaigns"""
    query = db.query(DirectMailCampaign)

    if status:
        query = query.filter(DirectMailCampaign.status == status)

    return query.order_by(DirectMailCampaign.created_at.desc()).limit(limit).all()


@router.post("/campaigns/{campaign_id}/execute")
async def execute_campaign_endpoint(
    campaign_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Execute a campaign (send all mailpieces)"""
    campaign = db.query(DirectMailCampaign).filter(
        DirectMailCampaign.id == campaign_id
    ).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    background_tasks.add_task(execute_campaign, campaign_id)

    return {"message": "Campaign execution started"}


# ==========================================================================
# TEMPLATES
# ==========================================================================

@router.post("/templates", response_model=DirectMailTemplateResponse)
async def create_template(
    data: DirectMailTemplateCreate,
    db: Session = Depends(get_db),
    agent_id: int = Query(None, description="Agent ID (from auth)")
):
    """Create a new direct mail template"""
    if not agent_id:
        agent_id = 1

    template = DirectMailTemplate(
        agent_id=agent_id,
        name=data.name,
        description=data.description,
        template_type=data.template_type,
        campaign_type=data.campaign_type,
        front_html_template=data.front_html_template,
        back_html_template=data.back_html_template,
        default_postcard_size=data.default_postcard_size,
        default_color=data.default_color,
        default_double_sided=data.default_double_sided,
        required_variables=data.required_variables,
        is_active=data.is_active
    )

    db.add(template)
    db.commit()
    db.refresh(template)

    return template


@router.get("/templates", response_model=List[DirectMailTemplateResponse])
async def list_templates(
    template_type: Optional[str] = None,
    is_system: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List all templates"""
    query = db.query(DirectMailTemplate)

    if template_type:
        query = query.filter(DirectMailTemplate.template_type == template_type)
    if is_system is not None:
        query = query.filter(DirectMailTemplate.is_system_template == is_system)

    return query.filter(DirectMailTemplate.is_active == True).all()


@router.get("/templates/{template_id}", response_model=DirectMailTemplateResponse)
async def get_template(template_id: int, db: Session = Depends(get_db)):
    """Get template details"""
    template = db.query(DirectMailTemplate).filter(
        DirectMailTemplate.id == template_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return template


# ==========================================================================
# ADDRESS VERIFICATION
# ==========================================================================

@router.post("/verify-address", response_model=AddressVerificationResponse)
async def verify_address(data: AddressVerificationRequest):
    """Verify and standardize a US postal address"""
    lob_client = LobClient()
    try:
        result = await lob_client.verify_address(data.dict())
        await lob_client.close()

        return AddressVerificationResponse(
            original_address=data.dict(),
            verified_address=result,
            is_valid=True,
            deliverability=result.get("deliverability", "unknown")
        )
    except Exception as e:
        return AddressVerificationResponse(
            original_address=data.dict(),
            verified_address={},
            is_valid=False,
            deliverability="undeliverable"
        )


# ==========================================================================
# VOICE ENDPOINTS
# ==========================================================================

@router.get("/postcards/{mailpiece_id}/voice", response_model=DirectMailVoiceSummary)
async def get_postcard_voice_summary(mailpiece_id: int, db: Session = Depends(get_db)):
    """Get voice-friendly summary of postcard status for TTS"""
    mailpiece = db.query(DirectMail).filter(
        DirectMail.id == mailpiece_id,
        DirectMail.mail_type == MailType.POSTCARD
    ).first()

    if not mailpiece:
        raise HTTPException(status_code=404, detail="Postcard not found")

    # Build voice summary
    recipient = mailpiece.to_address.get("name", "Recipient")
    status_voice = mailpiece.mail_status.value.replace("_", " ")

    tracking_summary = None
    if mailpiece.tracking_events:
        latest_event = mailpiece.tracking_events[-1] if mailpiece.tracking_events else None
        if latest_event:
            tracking_summary = f"{latest_event.get('status', 'unknown')} on {latest_event.get('timestamp', '')}"

    return DirectMailVoiceSummary(
        id=mailpiece.id,
        mail_type="postcard",
        status=status_voice,
        recipient=recipient,
        campaign=mailpiece.campaign_name,
        sent_date=mailpiece.created_at.strftime("%B %d, %Y") if mailpiece.created_at else None,
        delivery_status="delivered" if mailpiece.mail_status == MailStatus.DELIVERED else "in transit",
        tracking_summary=tracking_summary
    )


# ==========================================================================
# BACKGROUND TASKS
# ==========================================================================

async def send_postcard_to_lob(mailpiece_id: int, data: dict, agent_id: int):
    """Background task to send postcard to Lob"""
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        mailpiece = db.query(DirectMail).filter(DirectMail.id == mailpiece_id).first()
        if not mailpiece:
            return

        lob_client = LobClient()

        # Send postcard
        result = await lob_client.create_postcard(
            to_address=mailpiece.to_address,
            from_address=mailpiece.from_address,
            front_html=mailpiece.front_html,
            back_html=mailpiece.back_html or "",
            size=mailpiece.postcard_size.value if mailpiece.postcard_size else "4x6",
            merge_variables=mailpiece.merge_variables,
            send_after=mailpiece.send_after
        )

        # Update mailpiece with Lob response
        mailpiece.lob_mailpiece_id = result.get("id")
        mailpiece.lob_object_id = result.get("id")
        mailpiece.estimated_cost = result.get("expected_cost", 0) / 100  # Convert cents to dollars
        mailpiece.tracking_url = result.get("url")
        mailpiece.mail_status = LobClient.map_lob_status(result.get("status"))

        db.commit()
        await lob_client.close()

    except Exception as e:
        # Update status to failed
        mailpiece.mail_status = MailStatus.FAILED
        mailpiece.description = f"Failed to send: {str(e)}"
        db.commit()

    finally:
        db.close()


async def send_letter_to_lob(mailpiece_id: int, data: dict, agent_id: int):
    """Background task to send letter to Lob"""
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        mailpiece = db.query(DirectMail).filter(DirectMail.id == mailpiece_id).first()
        if not mailpiece:
            return

        lob_client = LobClient()

        # Send letter
        result = await lob_client.create_letter(
            to_address=mailpiece.to_address,
            from_address=mailpiece.from_address,
            file_url=mailpiece.file_url,
            color=mailpiece.color,
            double_sided=mailpiece.double_sided,
            certified_mail=mailpiece.certified_mail,
            return_envelope=mailpiece.return_envelope,
            size=mailpiece.letter_size.value if mailpiece.letter_size else "letter",
            send_after=mailpiece.send_after
        )

        # Update mailpiece
        mailpiece.lob_mailpiece_id = result.get("id")
        mailpiece.lob_object_id = result.get("id")
        mailpiece.estimated_cost = result.get("expected_cost", 0) / 100
        mailpiece.tracking_url = result.get("url")
        mailpiece.mail_status = LobClient.map_lob_status(result.get("status"))

        db.commit()
        await lob_client.close()

    except Exception as e:
        mailpiece.mail_status = MailStatus.FAILED
        mailpiece.description = f"Failed to send: {str(e)}"
        db.commit()

    finally:
        db.close()


async def sync_mailpiece_status(mailpiece: DirectMail, db: Session):
    """Sync mailpiece status from Lob"""
    if not mailpiece.lob_mailpiece_id:
        return

    lob_client = LobClient()
    try:
        status = await lob_client.get_mailpiece(mailpiece.lob_mailpiece_id)
        await lob_client.close()

        # Update status
        mailpiece.mail_status = LobClient.map_lob_status(status.get("status"))
        mailpiece.tracking_events = status.get("tracking_events", [])
        mailpiece.tracking_url = status.get("url")

        if mailpiece.mail_status == MailStatus.DELIVERED:
            mailpiece.delivered_at = datetime.now()

        db.commit()

    except Exception:
        pass  # Don't fail if sync fails


async def execute_campaign(campaign_id: int):
    """Background task to execute a bulk campaign"""
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        campaign = db.query(DirectMailCampaign).filter(
            DirectMailCampaign.id == campaign_id
        ).first()

        if not campaign:
            return

        campaign.status = "sending"
        db.commit()

        # Get recipients and send mailpieces
        # TODO: Implement actual sending logic

        campaign.status = "completed"
        db.commit()

    except Exception as e:
        campaign.status = "failed"
        db.commit()

    finally:
        db.close()


# ==========================================================================
# CSV IMPORT FOR CONTACTS
# ==========================================================================

@router.post("/import-csv")
async def import_contacts_csv(
    file: UploadFile = File(..., description="CSV file with contacts"),
    template: str = Query("interested_in_selling", description="Template to use for campaign"),
    campaign_name: str = Query(None, description="Campaign name (optional)"),
    create_campaign: bool = Query(False, description="Create campaign after importing"),
    send_immediately: bool = Query(False, description="Send immediately after creating campaign"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    agent_id: int = Query(None, description="Agent ID (from auth)")
):
    """
    Import contacts from CSV file for direct mail campaigns.

    CSV Format (required columns):
    - name: Contact name
    - address: Street address
    - city: City
    - state: State (2-letter code)
    - zip_code: ZIP code

    Optional columns:
    - phone: Phone number
    - email: Email address
    - property_address: Property address (if different from mailing address)
    - notes: Additional notes

    Example CSV:
    ```csv
    name,address,city,state,zip_code,phone,email
    "John Doe","123 Main St","Miami","FL","33101","(555) 123-4567","john@example.com"
    "Jane Smith","456 Oak Ave","Miami","FL","33102","(555) 987-6543","jane@example.com"
    ```

    Campaign Naming:
    - If campaign_name is provided: Uses that name
    - If campaign_name is omitted and create_campaign=true: Auto-generates from CSV filename
      Example: "miami_condo_leads.csv" → "Miami Condo Leads - 2026-02-26"

    Returns:
        - contacts_created: Number of contacts imported
        - contacts_failed: Number of contacts that failed to import
        - contact_ids: List of created contact IDs
        - campaign_id: Campaign ID if create_campaign=true
        - campaign_name: Name of the created campaign (if applicable)
        - errors: List of validation errors
    """
    # Default to agent_id=1 if not provided
    if not agent_id:
        agent_id = 1

    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="File must be a CSV file"
        )

    # Auto-generate campaign name from filename if not provided
    if not campaign_name and create_campaign:
        # Extract filename without .csv extension
        filename_base = file.filename.replace('.csv', '').replace('_', ' ').replace('-', ' ')
        # Capitalize first letter of each word
        campaign_name = filename_base.title()
        # Add timestamp for uniqueness
        campaign_name = f"{campaign_name} - {datetime.now().strftime('%Y-%m-%d')}"

    # Read CSV content
    contents = await file.read()

    # Parse CSV
    contacts_imported = []
    contacts_failed = []
    errors = []

    try:
        # Decode and parse CSV
        csv_text = contents.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_text))

        # Validate required columns
        required_columns = ['name', 'address', 'city', 'state', 'zip_code']
        csv_columns = csv_reader.fieldnames

        missing_columns = set(required_columns) - set(csv_columns)
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_columns)}. Required: {', '.join(required_columns)}"
            )

        # Process each row
        for row_num, row in enumerate(csv_reader, start=1):
            try:
                # Validate required fields
                if not row.get('name') or not row.get('name').strip():
                    errors.append(f"Row {row_num}: Name is required")
                    contacts_failed.append(row_num)
                    continue

                if not row.get('address') or not row.get('address').strip():
                    errors.append(f"Row {row_num}: Address is required")
                    contacts_failed.append(row_num)
                    continue

                if not row.get('city') or not row.get('city').strip():
                    errors.append(f"Row {row_num}: City is required")
                    contacts_failed.append(row_num)
                    continue

                if not row.get('state') or not row.get('state').strip():
                    errors.append(f"Row {row_num}: State is required")
                    contacts_failed.append(row_num)
                    continue

                if not row.get('zip_code') or not row.get('zip_code').strip():
                    errors.append(f"Row {row_num}: ZIP code is required")
                    contacts_failed.append(row_num)
                    continue

                # Validate state is 2 characters
                state = row['state'].strip()
                if len(state) != 2:
                    errors.append(f"Row {row_num}: State must be 2-letter code (e.g., 'FL', 'CA')")
                    contacts_failed.append(row_num)
                    continue

                # Create contact
                contact = Contact(
                    agent_id=agent_id,
                    name=row['name'].strip(),
                    address=row['address'].strip(),
                    city=row['city'].strip(),
                    state=state,
                    zip_code=row['zip_code'].strip(),
                    phone=row.get('phone', '').strip() if row.get('phone') else None,
                    email=row.get('email', '').strip() if row.get('email') else None,
                    notes=row.get('notes', '').strip() if row.get('notes') else None,
                    property_id=None  # Can be linked later
                )

                db.add(contact)
                db.flush()  # Get the ID without committing

                contacts_imported.append({
                    "row": row_num,
                    "contact_id": contact.id,
                    "name": contact.name,
                    "address": f"{contact.address}, {contact.city}, {contact.state} {contact.zip_code}"
                })

            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
                contacts_failed.append(row_num)
                continue

        # Commit all contacts
        db.commit()

        # Create campaign if requested
        campaign_id = None
        if create_campaign and contacts_imported:
            contact_ids = [c["contact_id"] for c in contacts_imported]

            campaign = DirectMailCampaign(
                agent_id=agent_id,
                name=campaign_name,
                description=f"Campaign created from CSV upload with {len(contact_ids)} contacts",
                campaign_type=template,
                mail_type=MailType.POSTCARD,
                template_id=None,
                target_contact_ids=contact_ids,
                filters={"csv_import": True},
                color=True,
                double_sided=True,
                send_immediately=send_immediately,
                total_recipients=len(contact_ids),
                sent_count=0,
                delivered_count=0,
                failed_count=0,
                total_cost=0.0,
                status="draft"
            )

            db.add(campaign)
            db.commit()
            db.refresh(campaign)

            campaign_id = campaign.id

            # Send immediately if requested
            if send_immediately and background_tasks:
                background_tasks.add_task(execute_campaign, campaign.id)

        return {
            "contacts_created": len(contacts_imported),
            "contacts_failed": len(contacts_failed),
            "contact_ids": [c["contact_id"] for c in contacts_imported],
            "contacts": contacts_imported,
            "campaign_id": campaign_id,
            "campaign_name": campaign.name if create_campaign and campaign_id else None,
            "errors": errors[:10],  # Return first 10 errors
            "message": f"Imported {len(contacts_imported)} contacts successfully. {len(contacts_failed)} failed."
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process CSV: {str(e)}"
        )


@router.get("/import-csv-template")
async def get_csv_import_template():
    """
    Get CSV import template and example data.

    Returns:
        - required_columns: List of required column names
        - optional_columns: List of optional column names
        - example_csv: Example CSV data
        - instructions: How to format the CSV
        - campaign_naming: How campaigns are auto-named
    """
    return {
        "required_columns": [
            "name",
            "address",
            "city",
            "state",
            "zip_code"
        ],
        "optional_columns": [
            "phone",
            "email",
            "property_address",
            "notes"
        ],
        "example_csv": """name,address,city,state,zip_code,phone,email,property_address,notes
"John Doe","123 Main St","Miami","FL","33101","(555) 123-4567","john@example.com","123 Main St","Interested in selling"
"Jane Smith","456 Oak Ave","Miami","FL","33102","(555) 987-6543","jane@example.com","","Price reduction inquiry"
"Bob Johnson","789 Pine Rd","Miami","FL","33103","","bob@example.com","","Expired listing follow-up"
"Alice Williams","321 Elm St","Miami","FL","33104","(555) 555-1234","alice@example.com","","Cold call from FSBO site"
"Charlie Brown","654 Maple Dr","Miami","FL","33105","(555) 678-9012","charlie@example.com","","Past client re-engagement\"""",
        "instructions": [
            "1. Create a CSV file with the columns listed above",
            "2. Include at minimum: name, address, city, state, zip_code",
            "3. Optional: phone, email, property_address, notes",
            "4. Save as UTF-8 encoded CSV file",
            "5. Name your CSV file descriptively (e.g., 'miami_condo_leads.csv')",
            "6. Upload to POST /direct-mail/import-csv",
            "7. Optionally set create_campaign=true to auto-create campaign",
            "8. Optionally set send_immediately=true to send right away"
        ],
        "campaign_naming": {
            "description": "Campaigns are automatically named based on your CSV filename",
            "examples": [
                "miami_condo_leads.csv → Miami Condo Leads - 2026-02-26",
                "expired_listings_march.csv → Expired Listings March - 2026-02-26",
                "fsbo_brooklyn.csv → Fsbo Brooklyn - 2026-02-26"
            ],
            "custom_name": "Override by adding ?campaign_name=My Custom Name to the URL"
        },
        "use_cases": [
            "Import leads from web scraping tools",
            "Upload FSBO (For Sale By Owner) leads",
            "Import expired listings for follow-up",
            "Upload client lists from other sources",
            "Import door-knocking results",
            "Import open house attendee lists",
            "Create neighborhood farming lists"
        ]
    }


@router.post("/verify-csv")
async def verify_csv_before_import(
    file: UploadFile = File(..., description="CSV file to verify"),
    db: Session = Depends(get_db)
):
    """
    Verify CSV file before importing without actually importing.

    Validates:
    - File format
    - Required columns
    - Data quality
    - Address format
    - Phone/email format

    Returns:
        - is_valid: Whether CSV is valid
        - total_rows: Total number of rows
        - valid_rows: Number of valid rows
        - invalid_rows: Number of invalid rows
        - errors: List of validation errors
        - preview: First 5 valid contacts
    """
    if not file.filename.endswith('.csv'):
        return {
            "is_valid": False,
            "error": "File must be a CSV file"
        }

    try:
        contents = await file.read()
        csv_text = contents.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_text))

        required_columns = ['name', 'address', 'city', 'state', 'zip_code']
        csv_columns = csv_reader.fieldnames

        # Check required columns
        missing_columns = set(required_columns) - set(csv_columns)
        if missing_columns:
            return {
                "is_valid": False,
                "error": f"Missing required columns: {', '.join(missing_columns)}",
                "required_columns": required_columns,
                "found_columns": csv_columns
            }

        # Validate rows
        valid_rows = []
        invalid_rows = []
        errors = []

        for row_num, row in enumerate(csv_reader, start=1):
            row_errors = []

            # Validate each field
            if not row.get('name') or not row.get('name').strip():
                row_errors.append("Name is required")

            if not row.get('address') or not row.get('address').strip():
                row_errors.append("Address is required")

            if not row.get('city') or not row.get('city').strip():
                row_errors.append("City is required")

            if not row.get('state') or not row.get('state').strip():
                row_errors.append("State is required")
            elif len(row['state'].strip()) != 2:
                row_errors.append("State must be 2-letter code")

            if not row.get('zip_code') or not row.get('zip_code').strip():
                row_errors.append("ZIP code is required")

            # Phone format validation (if provided)
            if row.get('phone') and row.get('phone').strip():
                phone = row['phone'].strip()
                # Remove common formatting
                phone_clean = phone.replace('(', '').replace(')', '').replace('-', '').replace(' ', '')
                if not phone_clean.isdigit() or len(phone_clean) < 10:
                    row_errors.append("Invalid phone format")

            # Email format validation (if provided)
            if row.get('email') and row.get('email').strip():
                email = row['email'].strip()
                if '@' not in email or '.' not in email.split('@')[1]:
                    row_errors.append("Invalid email format")

            if row_errors:
                invalid_rows.append({"row": row_num, "errors": row_errors})
                errors.append(f"Row {row_num}: {', '.join(row_errors)}")
            else:
                valid_rows.append({
                    "row": row_num,
                    "name": row['name'].strip(),
                    "address": f"{row['address'].strip()}, {row['city'].strip()}, {row['state'].strip()} {row['zip_code'].strip()}",
                    "phone": row.get('phone', '').strip(),
                    "email": row.get('email', '').strip()
                })

        # Return validation results
        return {
            "is_valid": len(invalid_rows) == 0,
            "total_rows": len(valid_rows) + len(invalid_rows),
            "valid_rows": len(valid_rows),
            "invalid_rows": len(invalid_rows),
            "errors": errors[:50],  # First 50 errors
            "preview": valid_rows[:5],  # First 5 valid contacts
        }

    except Exception as e:
        return {
            "is_valid": False,
            "error": f"Failed to parse CSV: {str(e)}"
        }
