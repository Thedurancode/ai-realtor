"""
Property Website Builder API

AI-powered landing page generation for properties
Voice-activated: "Create a landing page for property 5"
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Form
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
    name: str = Form(...),
    email: str = Form(...),
    phone: Optional[str] = Form(None),
    message: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Public endpoint to submit contact form from published website

    Tracks submission as analytics event and returns success response
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

    # Track form submission
    analytics = WebsiteAnalytics(
        website_id=website.id,
        event_type="contact_form_submit",
        event_data={
            "name": name,
            "email": email,
            "phone": phone,
            "message": message
        },
        created_at=datetime.utcnow()
    )
    db.add(analytics)
    db.commit()

    # TODO: Send email notification to agent
    # TODO: Create lead in database
    # TODO: Send confirmation email to submitter

    return {
        "success": True,
        "message": "Thank you for your inquiry! We'll be in touch soon."
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
