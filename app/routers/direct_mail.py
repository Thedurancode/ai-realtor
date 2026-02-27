"""
Direct Mail API Router

Endpoints for sending postcards, letters, and checks via Lob.com
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.direct_mail import (
    DirectMail,
    DirectMailTemplate,
    DirectMailCampaign,
    MailType,
    MailStatus
)
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
