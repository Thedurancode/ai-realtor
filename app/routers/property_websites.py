"""
Property Website Builder API

AI-powered landing page generation for properties
Voice-activated: "Create a landing page for property 5"
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Form, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import re
import string
import random

from app.database import get_db
from app.models.property import Property
from app.models.agent import Agent
from app.models.property_website import PropertyWebsite, WebsiteAnalytics
from app.services.website_generator import WebsiteGeneratorService

router = APIRouter(prefix="/properties/{property_id}/websites", tags=["Property Websites"])


@router.post("/", response_model=dict)
async def create_property_website(
    property_id: int,
    website_type: str = "landing_page",
    template: str = "modern",
    custom_name: Optional[str] = None,
    theme_overrides: Optional[dict] = None,
    agent_id: int = Query(..., description="Agent ID"),
    db: Session = Depends(get_db)
):
    """
    Create an AI-generated landing page for a property

    Voice command examples:
    - "Create a landing page for property 5"
    - "Generate a luxury website for the Hillsborough property"
    - "Build a modern single-page site for 123 Main St"
    """
    # Verify property exists and belongs to agent
    property_obj = db.query(Property).filter(
        Property.id == property_id,
        Property.agent_id == agent_id
    ).first()

    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")

    # Generate website content using AI
    generator = WebsiteGeneratorService(db)
    content = await generator.generate_website_content(property_obj, template)

    # Create website slug
    base_slug = f"{property_obj.address}-{property_obj.city}".lower().replace(" ", "-")
    slug = generate_unique_slug(db, base_slug)

    # Create website record
    website = PropertyWebsite(
        property_id=property_id,
        agent_id=agent_id,
        website_name=custom_name or f"{property_obj.address} - {property_obj.city} Landing Page",
        website_slug=slug,
        website_type=website_type,
        template=template,
        theme=theme_overrides or content.get("theme"),
        content=content,
        is_published=False
    )

    db.add(website)
    db.commit()
    db.refresh(website)

    return {
        "id": website.id,
        "website_name": website.website_name,
        "website_slug": website.website_slug,
        "website_url": f"/websites/{website.website_slug}",
        "website_type": website.website_type,
        "template": website.template,
        "content": website.content,
        "is_published": website.is_published,
        "created_at": website.created_at.isoformat()
    }


@router.get("/", response_model=List[dict])
async def list_property_websites(
    property_id: int,
    agent_id: int = Query(..., description="Agent ID"),
    db: Session = Depends(get_db)
):
    """List all websites for a property"""
    # Verify property belongs to agent
    property_obj = db.query(Property).filter(
        Property.id == property_id,
        Property.agent_id == agent_id
    ).first()

    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")

    websites = db.query(PropertyWebsite).filter(
        PropertyWebsite.property_id == property_id
    ).order_by(PropertyWebsite.created_at.desc()).all()

    return [
        {
            "id": w.id,
            "website_name": w.website_name,
            "website_slug": w.website_slug,
            "website_url": f"/websites/{w.website_slug}",
            "website_type": w.website_type,
            "template": w.template,
            "is_published": w.is_published,
            "is_active": w.is_active,
            "published_at": w.published_at.isoformat() if w.published_at else None,
            "created_at": w.created_at.isoformat(),
            "views": count_website_views(db, w.id)
        }
        for w in websites
    ]


@router.get("/{website_id}", response_model=dict)
async def get_website(
    property_id: int,
    website_id: int,
    agent_id: int = Query(..., description="Agent ID"),
    db: Session = Depends(get_db)
):
    """Get website details"""
    website = db.query(PropertyWebsite).filter(
        PropertyWebsite.id == website_id,
        PropertyWebsite.property_id == property_id
    ).first()

    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    # Verify agent owns this property
    property_obj = db.query(Property).filter(
        Property.id == property_id,
        Property.agent_id == agent_id
    ).first()

    if not property_obj:
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "id": website.id,
        "property_id": website.property_id,
        "website_name": website.website_name,
        "website_slug": website.website_slug,
        "website_type": website.website_type,
        "template": website.template,
        "theme": website.theme,
        "content": website.content,
        "is_published": website.is_published,
        "is_active": website.is_active,
        "custom_domain": website.custom_domain,
        "published_at": website.published_at.isoformat() if website.published_at else None,
        "created_at": website.created_at.isoformat(),
        "updated_at": website.updated_at.isoformat(),
        "analytics": {
            "total_views": count_website_views(db, website.id),
            "form_submissions": count_website_events(db, website.id, "contact_form_submit"),
            "inquiries": count_website_events(db, website.id, "inquiry")
        }
    }


@router.put("/{website_id}", response_model=dict)
async def update_website(
    property_id: int,
    website_id: int,
    website_name: Optional[str] = None,
    theme: Optional[dict] = None,
    content_updates: Optional[dict] = None,
    agent_id: int = Query(..., description="Agent ID"),
    db: Session = Depends(get_db)
):
    """Update website content or settings"""
    website = db.query(PropertyWebsite).filter(
        PropertyWebsite.id == website_id,
        PropertyWebsite.property_id == property_id
    ).first()

    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    # Verify agent owns this property
    property_obj = db.query(Property).filter(
        Property.id == property_id,
        Property.agent_id == agent_id
    ).first()

    if not property_obj:
        raise HTTPException(status_code=403, detail="Access denied")

    # Update fields
    if website_name:
        website.website_name = website_name

    if theme:
        website.theme = {**website.theme, **theme}

    if content_updates:
        website.content = {**website.content, **content_updates}

    db.commit()
    db.refresh(website)

    return {
        "id": website.id,
        "website_name": website.website_name,
        "website_slug": website.website_slug,
        "updated_at": website.updated_at.isoformat()
    }


@router.post("/{website_id}/publish", response_model=dict)
async def publish_website(
    property_id: int,
    website_id: int,
    agent_id: int = Query(..., description="Agent ID"),
    db: Session = Depends(get_db)
):
    """
    Publish a website (make it publicly accessible)

    Voice command: "Publish the landing page for property 5"
    """
    website = db.query(PropertyWebsite).filter(
        PropertyWebsite.id == website_id,
        PropertyWebsite.property_id == property_id
    ).first()

    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    # Verify agent owns this property
    property_obj = db.query(Property).filter(
        Property.id == property_id,
        Property.agent_id == agent_id
    ).first()

    if not property_obj:
        raise HTTPException(status_code=403, detail="Access denied")

    # Publish website
    website.is_published = True
    website.published_at = datetime.utcnow()
    db.commit()

    return {
        "id": website.id,
        "website_name": website.website_name,
        "website_slug": website.website_slug,
        "website_url": f"/websites/{website.website_slug}",
        "is_published": True,
        "published_at": website.published_at.isoformat()
    }


@router.post("/{website_id}/unpublish", response_model=dict)
async def unpublish_website(
    property_id: int,
    website_id: int,
    agent_id: int = Query(..., description="Agent ID"),
    db: Session = Depends(get_db)
):
    """Unpublish a website (make it private)"""
    website = db.query(PropertyWebsite).filter(
        PropertyWebsite.id == website_id,
        PropertyWebsite.property_id == property_id
    ).first()

    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    # Verify agent owns this property
    property_obj = db.query(Property).filter(
        Property.id == property_id,
        Property.agent_id == agent_id
    ).first()

    if not property_obj:
        raise HTTPException(status_code=403, detail="Access denied")

    website.is_published = False
    db.commit()

    return {
        "id": website.id,
        "is_published": False,
        "message": "Website unpublished successfully"
    }


@router.delete("/{website_id}", response_model=dict)
async def delete_website(
    property_id: int,
    website_id: int,
    agent_id: int = Query(..., description="Agent ID"),
    db: Session = Depends(get_db)
):
    """Delete a website permanently"""
    website = db.query(PropertyWebsite).filter(
        PropertyWebsite.id == website_id,
        PropertyWebsite.property_id == property_id
    ).first()

    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    # Verify agent owns this property
    property_obj = db.query(Property).filter(
        Property.id == property_id,
        Property.agent_id == agent_id
    ).first()

    if not property_obj:
        raise HTTPException(status_code=403, detail="Access denied")

    website_slug = website.website_slug
    db.delete(website)
    db.commit()

    return {
        "message": f"Website '{website_slug}' deleted successfully"
    }


@router.get("/{website_id}/analytics", response_model=dict)
async def get_website_analytics(
    property_id: int,
    website_id: int,
    event_type: Optional[str] = None,
    days: int = 30,
    agent_id: int = Query(..., description="Agent ID"),
    db: Session = Depends(get_db)
):
    """
    Get analytics for a website

    Voice command: "Show analytics for the landing page on property 5"
    """
    from datetime import timedelta

    website = db.query(PropertyWebsite).filter(
        PropertyWebsite.id == website_id,
        PropertyWebsite.property_id == property_id
    ).first()

    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    # Verify agent owns this property
    property_obj = db.query(Property).filter(
        Property.id == property_id,
        Property.agent_id == agent_id
    ).first()

    if not property_obj:
        raise HTTPException(status_code=403, detail="Access denied")

    # Query analytics
    query = db.query(WebsiteAnalytics).filter(
        WebsiteAnalytics.website_id == website_id
    )

    if event_type:
        query = query.filter(WebsiteAnalytics.event_type == event_type)

    # Filter by date range
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    query = query.filter(WebsiteAnalytics.created_at >= cutoff_date)

    analytics = query.order_by(WebsiteAnalytics.created_at.desc()).all()

    # Calculate stats
    total_events = len(analytics)
    events_by_type = {}
    for event in analytics:
        events_by_type[event.event_type] = events_by_type.get(event.event_type, 0) + 1

    # Get recent events
    recent_events = analytics[:10]

    return {
        "website_id": website_id,
        "website_name": website.website_name,
        "period_days": days,
        "total_events": total_events,
        "events_by_type": events_by_type,
        "recent_events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "event_data": e.event_data,
                "created_at": e.created_at.isoformat()
            }
            for e in recent_events
        ]
    }


# Public endpoint to view published website (no auth required)
@router.get("/view/{website_slug}", include_in_schema=False)
async def view_published_website(
    website_slug: str,
    track_view: bool = True,
    db: Session = Depends(get_db)
):
    """
    Public endpoint to view a published website

    Renders the HTML for the AI-generated landing page
    """
    # Find website by slug
    website = db.query(PropertyWebsite).filter(
        PropertyWebsite.website_slug == website_slug
    ).first()

    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    # Check if published
    if not website.is_published or not website.is_active:
        raise HTTPException(status_code=404, detail="Website is not available")

    # Track view if enabled
    if track_view:
        analytics = WebsiteAnalytics(
            website_id=website.id,
            event_type="view",
            event_data={},
            created_at=datetime.utcnow()
        )
        db.add(analytics)
        db.commit()

    # Return HTML content
    from app.services.website_renderer import WebsiteRenderer
    renderer = WebsiteRenderer(db)
    html_content = await renderer.render_website(website)

    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)


@router.post("/view/{website_slug}/submit", include_in_schema=False)
async def submit_contact_form(
    website_slug: str,
    request: Request,  # Add to get visitor info
    name: str = Form(...),
    email: str = Form(...),
    phone: Optional[str] = Form(None),
    message: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Public endpoint to submit contact form from published website

    Automatically:
    - Tracks submission as analytics event
    - Creates Contact record in database
    - Sends notification to agent
    - Sends confirmation email to submitter (if configured)

    Default behavior - no configuration needed!
    """

    # Find website by slug
    website = db.query(PropertyWebsite).filter(
        PropertyWebsite.website_slug == website_slug
    ).first()

    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    # Check if published
    if not website.is_published or not website.is_active:
        raise HTTPException(status_code=404, detail="Website is not available")

    from app.models.contact import Contact, ContactRole
    from app.models.notification import Notification, NotificationType, NotificationPriority
    from app.services.email_service import email_service

    # Get visitor info
    visitor_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")
    referrer = request.headers.get("referer", "")

    # 1. Track form submission as analytics event
    analytics = WebsiteAnalytics(
        website_id=website.id,
        event_type="contact_form_submit",
        event_data={
            "name": name,
            "email": email,
            "phone": phone,
            "message": message
        },
        visitor_ip=visitor_ip,
        user_agent=user_agent,
        referrer=referrer,
        created_at=datetime.utcnow()
    )
    db.add(analytics)

    # 2. Create Contact record (auto-linked to property)
    # Check if contact with this email already exists for this property
    existing_contact = db.query(Contact).filter(
        Contact.property_id == website.property_id,
        Contact.email == email
    ).first()

    if not existing_contact:
        contact = Contact(
            property_id=website.property_id,
            name=name,
            email=email,
            phone=phone,
            role=ContactRole.BUYER,  # Default to buyer for website inquiries
            notes=f"Submitted via website landing page: {website.website_name}\n\nMessage: {message or 'No message provided'}"
        )
        db.add(contact)
        db.flush()  # Get contact.id without committing yet
    else:
        # Update existing contact with new inquiry
        contact = existing_contact
        if not contact.phone and phone:
            contact.phone = phone
        existing_notes = contact.notes or ""
        contact.notes = f"{existing_notes}\n\n--- New Inquiry ---\nSubmitted via website: {website.website_name}\nMessage: {message or 'No message provided'}"

    # 3. Create notification for agent
    notification = Notification(
        agent_id=website.agent_id,
        type=NotificationType.NEW_LEAD,
        priority=NotificationPriority.HIGH,
        title=f"New Lead from Website: {name}",
        message=f"{name} ({email}) submitted an inquiry via the landing page for {website.website_name}.\n\nPhone: {phone or 'Not provided'}\nMessage: {message or 'No message provided'}",
        property_id=website.property_id,
        link=f"/properties/{website.property_id}/websites/{website.id}/analytics"
    )
    db.add(notification)

    # Commit all changes
    db.commit()

    # 4. Send email notification to agent (if Resend is configured)
    try:
        agent = website.agent
        if agent and email_service.enabled:
            email_service.send_alert_notification(
                to=[agent.email],
                alert_name="New Website Lead",
                alert_message=f"{name} has submitted an inquiry via your property landing page.",
                metric_name="website_leads",
                metric_value=1,
                severity="high",
                additional_context={
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "message": message,
                    "property_id": website.property_id,
                    "website_name": website.website_name,
                    "lead_source": "website_form"
                }
            )
    except Exception as e:
        # Don't fail the request if email fails
        print(f"Warning: Failed to send lead notification email: {e}")

    # 5. Send confirmation email to submitter (optional - only if configured)
    try:
        if email_service.enabled:
            email_service.send_email(
                to=email,
                subject=f"Thank you for your inquiry!",
                html_content=f"""
                <h2>Thank You for Your Interest!</h2>
                <p>Hi {name},</p>
                <p>Thank you for submitting an inquiry about <strong>{website.website_name}</strong>.</p>
                <p>We have received your message and will be in touch with you shortly.</p>
                <p><strong>Your Message:</strong></p>
                <p>{message or 'No message provided'}</p>
                <p>Best regards,<br>The Team</p>
                """,
                tags=[{"name": "website_form", "value": "confirmation"}]
            )
    except Exception as e:
        # Don't fail the request if confirmation email fails
        print(f"Warning: Failed to send confirmation email: {e}")

    return {
        "success": True,
        "message": "Thank you for your inquiry! We'll be in touch soon.",
        "contact_id": contact.id,
        "lead_created": not existing_contact
    }


@router.post("/{website_id}/track-event", response_model=dict)
async def track_website_event(
    website_id: int,
    event_type: str,
    event_data: Optional[dict] = None,
    db: Session = Depends(get_db)
):
    """
    Track custom analytics events for a website

    Tracks button clicks, scroll depth, etc.
    """
    website = db.query(PropertyWebsite).filter(
        PropertyWebsite.id == website_id
    ).first()

    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    # Track event
    analytics = WebsiteAnalytics(
        website_id=website.id,
        event_type=event_type,
        event_data=event_data or {},
        created_at=datetime.utcnow()
    )
    db.add(analytics)
    db.commit()

    return {
        "success": True,
        "event_type": event_type,
        "tracked_at": datetime.utcnow().isoformat()
    }


# Helper functions
def generate_unique_slug(db: Session, base_slug: str, attempt: int = 0) -> str:
    """Generate a unique URL slug"""
    slug = base_slug
    if attempt > 0:
        slug = f"{base_slug}-{attempt}"

    existing = db.query(PropertyWebsite).filter(
        PropertyWebsite.website_slug == slug
    ).first()

    if existing:
        return generate_unique_slug(db, base_slug, attempt + 1)

    return slug


def count_website_views(db: Session, website_id: int) -> int:
    """Count total views for a website"""
    return db.query(WebsiteAnalytics).filter(
        WebsiteAnalytics.website_id == website_id,
        WebsiteAnalytics.event_type == "view"
    ).count()


def count_website_events(db: Session, website_id: int, event_type: str) -> int:
    """Count specific events for a website"""
    return db.query(WebsiteAnalytics).filter(
        WebsiteAnalytics.website_id == website_id,
        WebsiteAnalytics.event_type == event_type
    ).count()
