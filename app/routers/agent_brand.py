from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, List
import json
import os
from datetime import datetime

from app.database import get_db
from app.models.agent import Agent
from app.models.agent_brand import AgentBrand
from pydantic import BaseModel, Field
from typing import Dict, Any, List as ListType

router = APIRouter(prefix="/agent-brand", tags=["Agent Brand"])


# Pydantic schemas
class AgentBrandCreate(BaseModel):
    company_name: Optional[str] = None
    tagline: Optional[str] = None
    logo_url: Optional[str] = None
    website_url: Optional[str] = None

    bio: Optional[str] = None
    about_us: Optional[str] = None
    specialties: Optional[ListType[str]] = None
    service_areas: Optional[ListType[Dict[str, Any]]] = None
    languages: Optional[ListType[str]] = None

    primary_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    secondary_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    accent_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    background_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    text_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')

    social_media: Optional[Dict[str, str]] = None
    display_phone: Optional[str] = None
    display_email: Optional[str] = None
    office_address: Optional[str] = None
    office_phone: Optional[str] = None

    license_display_name: Optional[str] = None
    license_number: Optional[str] = None
    license_states: Optional[ListType[str]] = None

    show_profile: Optional[bool] = True
    show_contact_info: Optional[bool] = True
    show_social_media: Optional[bool] = True

    headshot_url: Optional[str] = None
    banner_url: Optional[str] = None
    company_badge_url: Optional[str] = None

    email_template_style: Optional[str] = "modern"
    report_logo_placement: Optional[str] = "top-left"

    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    keywords: Optional[ListType[str]] = None

    google_analytics_id: Optional[str] = None
    facebook_pixel_id: Optional[str] = None


class AgentBrandUpdate(BaseModel):
    company_name: Optional[str] = None
    tagline: Optional[str] = None
    logo_url: Optional[str] = None
    website_url: Optional[str] = None

    bio: Optional[str] = None
    about_us: Optional[str] = None
    specialties: Optional[ListType[str]] = None
    service_areas: Optional[ListType[Dict[str, Any]]] = None
    languages: Optional[ListType[str]] = None

    primary_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    secondary_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    accent_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    background_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    text_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')

    social_media: Optional[Dict[str, str]] = None
    display_phone: Optional[str] = None
    display_email: Optional[str] = None
    office_address: Optional[str] = None
    office_phone: Optional[str] = None

    license_display_name: Optional[str] = None
    license_number: Optional[str] = None
    license_states: Optional[ListType[str]] = None

    show_profile: Optional[bool] = None
    show_contact_info: Optional[bool] = None
    show_social_media: Optional[bool] = None

    headshot_url: Optional[str] = None
    banner_url: Optional[str] = None
    company_badge_url: Optional[str] = None

    email_template_style: Optional[str] = None
    report_logo_placement: Optional[str] = None

    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    keywords: Optional[ListType[str]] = None

    google_analytics_id: Optional[str] = None
    facebook_pixel_id: Optional[str] = None


class AgentBrandResponse(BaseModel):
    id: int
    agent_id: int
    company_name: Optional[str]
    tagline: Optional[str]
    logo_url: Optional[str]
    website_url: Optional[str]

    bio: Optional[str]
    about_us: Optional[str]
    specialties: Optional[ListType[str]]
    service_areas: Optional[ListType[Dict[str, Any]]]
    languages: Optional[ListType[str]]

    primary_color: Optional[str]
    secondary_color: Optional[str]
    accent_color: Optional[str]
    background_color: Optional[str]
    text_color: Optional[str]

    social_media: Optional[Dict[str, str]]
    display_phone: Optional[str]
    display_email: Optional[str]
    office_address: Optional[str]
    office_phone: Optional[str]

    license_display_name: Optional[str]
    license_number: Optional[str]
    license_states: Optional[ListType[str]]

    show_profile: bool
    show_contact_info: bool
    show_social_media: bool

    headshot_url: Optional[str]
    banner_url: Optional[str]
    company_badge_url: Optional[str]

    email_template_style: str
    report_logo_placement: str

    meta_title: Optional[str]
    meta_description: Optional[str]
    keywords: Optional[ListType[str]]

    google_analytics_id: Optional[str]
    facebook_pixel_id: Optional[str]

    created_at: datetime
    updated_at: Optional[datetime]

    voice_summary: Optional[str] = None

    class Config:
        from_attributes = True


def get_agent_brand(db: Session, agent_id: int):
    """Get agent brand by agent_id"""
    return db.query(AgentBrand).filter(AgentBrand.agent_id == agent_id).first()


# Endpoints

@router.post("/{agent_id}", response_model=AgentBrandResponse)
def create_agent_brand(
    agent_id: int,
    brand_data: AgentBrandCreate,
    db: Session = Depends(get_db)
):
    """Create or update agent brand profile"""
    # Verify agent exists
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Check if brand already exists
    existing_brand = get_agent_brand(db, agent_id)
    if existing_brand:
        raise HTTPException(status_code=400, detail="Brand profile already exists. Use PUT to update.")

    # Create new brand
    brand_data_dict = brand_data.model_dump(exclude_unset=True)

    brand = AgentBrand(agent_id=agent_id, **brand_data_dict)
    db.add(brand)
    db.commit()
    db.refresh(brand)

    # Generate voice summary
    voice_summary = f"Brand profile created for {agent.name}. {brand.company_name or 'Personal brand'} is now active."

    return AgentBrandResponse(
        **brand.__dict__,
        voice_summary=voice_summary
    )


@router.get("/{agent_id}", response_model=AgentBrandResponse)
def get_agent_brand_endpoint(
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Get agent brand profile"""
    # Verify agent exists
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    brand = get_agent_brand(db, agent_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand profile not found")

    # Generate voice summary
    has_branding = bool(brand.logo_url or brand.primary_color or brand.company_name)
    voice_summary = f"{agent.name}'s brand profile. "
    if has_branding:
        voice_summary += f"Company: {brand.company_name or 'Personal brand'}. "
        if brand.tagline:
            voice_summary += f"Tagline: {brand.tagline}. "
        if brand.show_profile:
            voice_summary += "Profile is public."
        else:
            voice_summary += "Profile is private."
    else:
        voice_summary += "No branding set up yet."

    return AgentBrandResponse(
        **brand.__dict__,
        voice_summary=voice_summary
    )


@router.put("/{agent_id}", response_model=AgentBrandResponse)
def update_agent_brand(
    agent_id: int,
    brand_data: AgentBrandUpdate,
    db: Session = Depends(get_db)
):
    """Update agent brand profile"""
    brand = get_agent_brand(db, agent_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand profile not found")

    # Update only provided fields
    update_data = brand_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(brand, field, value)

    db.commit()
    db.refresh(brand)

    # Generate voice summary
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    voice_summary = f"{agent.name}'s brand profile updated successfully."

    return AgentBrandResponse(
        **brand.__dict__,
        voice_summary=voice_summary
    )


@router.patch("/{agent_id}/colors", response_model=AgentBrandResponse)
def update_brand_colors(
    agent_id: int,
    primary_color: Optional[str] = None,
    secondary_color: Optional[str] = None,
    accent_color: Optional[str] = None,
    background_color: Optional[str] = None,
    text_color: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Quick update for brand colors"""
    brand = get_agent_brand(db, agent_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand profile not found")

    # Validate hex colors
    colors = {
        'primary_color': primary_color,
        'secondary_color': secondary_color,
        'accent_color': accent_color,
        'background_color': background_color,
        'text_color': text_color
    }

    for field, value in colors.items():
        if value:
            # Validate hex format
            if not value.startswith('#') or len(value) != 7:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid {field}: must be hex color (e.g., #FF5733)"
                )
            setattr(brand, field, value)

    db.commit()
    db.refresh(brand)

    voice_summary = f"Brand colors updated for {brand.company_name or 'your profile'}."

    return AgentBrandResponse(
        **brand.__dict__,
        voice_summary=voice_summary
    )


@router.post("/{agent_id}/logo", response_model=AgentBrandResponse)
async def upload_logo(
    agent_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload brand logo"""
    brand = get_agent_brand(db, agent_id)
    if not brand:
        # Create brand if doesn't exist
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        brand = AgentBrand(agent_id=agent_id)
        db.add(brand)

    # Save file (in production, use S3 or CDN)
    # For now, just store the filename
    file_extension = file.filename.split('.')[-1]
    logo_filename = f"logo_agent_{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}"

    # TODO: Actually save the file to storage service
    # For now, just set the URL
    brand.logo_url = f"/uploads/logos/{logo_filename}"

    db.commit()
    db.refresh(brand)

    voice_summary = f"Logo uploaded for {brand.company_name or 'your profile'}."

    return AgentBrandResponse(
        **brand.__dict__,
        voice_summary=voice_summary
    )


@router.get("/public/{agent_id}", response_model=Dict[str, Any])
def get_public_brand_profile(
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Get public-facing brand profile (respecting privacy settings)"""
    brand = get_agent_brand(db, agent_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand profile not found")

    if not brand.show_profile:
        raise HTTPException(status_code=403, detail="This profile is private")

    # Build public profile
    public_data = {
        "company_name": brand.company_name,
        "tagline": brand.tagline,
        "logo_url": brand.logo_url,
        "website_url": brand.website_url,
        "bio": brand.bio if brand.show_contact_info else None,
        "specialties": brand.specialties,
        "service_areas": brand.service_areas,
        "languages": brand.languages,
        "primary_color": brand.primary_color,
        "secondary_color": brand.secondary_color,
        "accent_color": brand.accent_color,
        "headshot_url": brand.headshot_url,
        "banner_url": brand.banner_url,
        "company_badge_url": brand.company_badge_url,
        "social_media": brand.social_media if brand.show_social_media else None,
        "display_phone": brand.display_phone if brand.show_contact_info else None,
        "display_email": brand.display_email if brand.show_contact_info else None,
        "office_address": brand.office_address if brand.show_contact_info else None,
        "license_display_name": brand.license_display_name,
        "license_number": brand.license_number,
        "license_states": brand.license_states,
    }

    return public_data


@router.delete("/{agent_id}")
def delete_agent_brand(
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Delete agent brand profile"""
    brand = get_agent_brand(db, agent_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand profile not found")

    agent_name = db.query(Agent).filter(Agent.id == agent_id).first().name

    db.delete(brand)
    db.commit()

    return {
        "message": f"Brand profile deleted for {agent_name}",
        "agent_id": agent_id,
        "voice_summary": f"Brand profile deleted for {agent_name}."
    }


@router.get("/colors/presets", response_model=List[Dict[str, Any]])
def get_color_presets():
    """Get pre-defined color schemes for branding"""
    presets = [
        {
            "name": "Professional Blue",
            "description": "Trustworthy and corporate",
            "primary": "#1E3A8A",
            "secondary": "#3B82F6",
            "accent": "#60A5FA",
            "background": "#F8FAFC",
            "text": "#1E293B"
        },
        {
            "name": "Modern Green",
            "description": "Fresh and eco-friendly",
            "primary": "#059669",
            "secondary": "#10B981",
            "accent": "#34D399",
            "background": "#F0FDF4",
            "text": "#064E3B"
        },
        {
            "name": "Luxury Gold",
            "description": "Premium and high-end",
            "primary": "#B45309",
            "secondary": "#D97706",
            "accent": "#F59E0B",
            "background": "#FFFBEB",
            "text": "#78350F"
        },
        {
            "name": "Bold Red",
            "description": "Energetic and attention-grabbing",
            "primary": "#DC2626",
            "secondary": "#EF4444",
            "accent": "#F87171",
            "background": "#FEF2F2",
            "text": "#7F1D1D"
        },
        {
            "name": "Minimalist Black",
            "description": "Sleek and modern",
            "primary": "#000000",
            "secondary": "#374151",
            "accent": "#6B7280",
            "background": "#FFFFFF",
            "text": "#000000"
        },
        {
            "name": "Ocean Teal",
            "description": "Calm and professional",
            "primary": "#0F766E",
            "secondary": "#14B8A6",
            "accent": "#2DD4BF",
            "background": "#F0FDFA",
            "text": "#042F2E"
        }
    ]

    return presets


@router.post("/{agent_id}/apply-preset")
def apply_color_preset(
    agent_id: int,
    preset_name: str,
    db: Session = Depends(get_db)
):
    """Apply a pre-defined color scheme"""
    brand = get_agent_brand(db, agent_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand profile not found")

    # Get preset
    presets = {
        "Professional Blue": {
            "primary": "#1E3A8A",
            "secondary": "#3B82F6",
            "accent": "#60A5FA",
            "background": "#F8FAFC",
            "text": "#1E293B"
        },
        "Modern Green": {
            "primary": "#059669",
            "secondary": "#10B981",
            "accent": "#34D399",
            "background": "#F0FDF4",
            "text": "#064E3B"
        },
        "Luxury Gold": {
            "primary": "#B45309",
            "secondary": "#D97706",
            "accent": "#F59E0B",
            "background": "#FFFBEB",
            "text": "#78350F"
        },
        "Bold Red": {
            "primary": "#DC2626",
            "secondary": "#EF4444",
            "accent": "#F87171",
            "background": "#FEF2F2",
            "text": "#7F1D1D"
        },
        "Minimalist Black": {
            "primary": "#000000",
            "secondary": "#374151",
            "accent": "#6B7280",
            "background": "#FFFFFF",
            "text": "#000000"
        },
        "Ocean Teal": {
            "primary": "#0F766E",
            "secondary": "#14B8A6",
            "accent": "#2DD4BF",
            "background": "#F0FDFA",
            "text": "#042F2E"
        }
    }

    if preset_name not in presets:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_name}' not found. Available: {', '.join(presets.keys())}")

    colors = presets[preset_name]
    brand.primary_color = colors["primary"]
    brand.secondary_color = colors["secondary"]
    brand.accent_color = colors["accent"]
    brand.background_color = colors["background"]
    brand.text_color = colors["text"]

    db.commit()
    db.refresh(brand)

    voice_summary = f"Applied {preset_name} color scheme to {brand.company_name or 'your profile'}."

    return AgentBrandResponse(
        **brand.__dict__,
        voice_summary=voice_summary
    )


@router.post("/{agent_id}/generate-preview")
def generate_brand_preview(
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Generate HTML preview of branded materials"""
    brand = get_agent_brand(db, agent_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand profile not found")

    # Generate HTML preview
    agent = db.query(Agent).filter(Agent.id == agent_id).first()

    # Color defaults
    primary = brand.primary_color or "#1E3A8A"
    secondary = brand.secondary_color or "#3B82F6"

    html_preview = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px;">
        <!-- Email Signature Preview -->
        <div style="border-left: 4px solid {primary}; padding-left: 15px; margin-bottom: 30px;">
            <h3 style="color: {primary}; margin: 0;">Email Signature</h3>
            <p style="margin: 10px 0;">
                <strong>{agent.name}</strong><br>
                {brand.company_name or 'Real Estate Professional'}<br>
                {brand.display_phone or ''}<br>
                {brand.display_email or ''}
            </p>
            <div style="margin-top: 10px;">
                {f'<a href="{brand.website_url}" style="color: {primary};">Website</a>' if brand.website_url else ''}
            </div>
        </div>

        <!-- Property Report Header -->
        <div style="background: {primary}; color: white; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
            <h2 style="margin: 0;">{brand.company_name or agent.name}</h2>
            {f'<p style="margin: 5px 0 0 0; opacity: 0.9;">{brand.tagline}</p>' if brand.tagline else ''}
        </div>

        <!-- Business Card Preview -->
        <div style="background: {secondary or '#f3f4f6'}; padding: 20px; border-radius: 8px;">
            <h3 style="color: {primary}; margin-top: 0;">Business Card</h3>
            <div style="display: flex; gap: 20px;">
                {f'<div style="width: 80px; height: 80px; background: #ddd; border-radius: 50%;"></div>' if brand.headshot_url else '<div style="width: 80px; height: 80px; background: #ddd; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px;">{agent.name[0]}</div>'}
                <div>
                    <strong style="color: {primary};">{agent.name}</strong><br>
                    {f'<em>{brand.tagline}</em><br>' if brand.tagline else ''}
                    {brand.display_phone or ''}<br>
                    {brand.display_email or ''}
                </div>
            </div>
        </div>
    </div>
    """

    return {
        "agent_id": agent_id,
        "html_preview": html_preview,
        "voice_summary": f"Generated brand preview for {agent.name}. {brand.company_name or 'Profile'} colors: {primary} primary, {secondary or 'default'} secondary."
    }


@router.get("/")
def list_all_brands(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all agent brands (admin only)"""
    brands = db.query(AgentBrand).offset(skip).limit(limit).all()
    total = db.query(AgentBrand).count()

    return {
        "total": total,
        "brands": [
            {
                "id": brand.id,
                "agent_id": brand.agent_id,
                "company_name": brand.company_name,
                "logo_url": brand.logo_url,
                "show_profile": brand.show_profile,
                "created_at": brand.created_at
            }
            for brand in brands
        ],
        "voice_summary": f"Found {total} brand profile{'s' if total != 1 else ''}."
    }
