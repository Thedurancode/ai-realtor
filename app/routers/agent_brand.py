from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, List
import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path

from app.database import get_db, SessionLocal
from app.models.agent import Agent
from app.models.agent_brand import AgentBrand
from app.models.property import Property
from app.models.talking_head_video import TalkingHeadVideo
from app.config import settings
from app.services.pvc_service import PVCService
from app.services.pexels_service import PexelsService
from app.services.talking_head_service import generate_talking_head_video
from app.services.shotstack_service import ShotstackService
from app.services.video_pipeline_service import run_property_video_pipeline, run_brand_video_pipeline
from app.models.property_video_job import PropertyVideoJob
from app.utils.file_storage import file_storage
from pydantic import BaseModel, Field
from typing import Dict, Any, List as ListType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-brand", tags=["Agent Brand"])

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac"}


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
    voice_sample_url: Optional[str] = None
    voice_clone_id: Optional[str] = None
    voice_clone_status: Optional[str] = None

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
    voice_sample_url: Optional[str] = None
    voice_clone_id: Optional[str] = None
    voice_clone_status: Optional[str] = None

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
    voice_sample_url: Optional[str]
    voice_clone_id: Optional[str]
    voice_clone_status: Optional[str]

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


# --- Helpers ---

def get_agent_brand(db: Session, agent_id: int):
    """Get agent brand by agent_id"""
    return db.query(AgentBrand).filter(AgentBrand.agent_id == agent_id).first()


def _brand_to_response(brand: AgentBrand, voice_summary: str = "") -> AgentBrandResponse:
    """Convert an AgentBrand model instance to an AgentBrandResponse."""
    return AgentBrandResponse(
        id=brand.id,
        agent_id=brand.agent_id,
        company_name=brand.company_name,
        tagline=brand.tagline,
        logo_url=brand.logo_url,
        website_url=brand.website_url,
        bio=brand.bio,
        about_us=brand.about_us,
        specialties=brand.specialties,
        service_areas=brand.service_areas,
        languages=brand.languages,
        primary_color=brand.primary_color,
        secondary_color=brand.secondary_color,
        accent_color=brand.accent_color,
        background_color=brand.background_color,
        text_color=brand.text_color,
        social_media=brand.social_media,
        display_phone=brand.display_phone,
        display_email=brand.display_email,
        office_address=brand.office_address,
        office_phone=brand.office_phone,
        license_display_name=brand.license_display_name,
        license_number=brand.license_number,
        license_states=brand.license_states,
        show_profile=brand.show_profile,
        show_contact_info=brand.show_contact_info,
        show_social_media=brand.show_social_media,
        headshot_url=brand.headshot_url,
        banner_url=brand.banner_url,
        company_badge_url=brand.company_badge_url,
        voice_sample_url=brand.voice_sample_url,
        voice_clone_id=brand.voice_clone_id,
        voice_clone_status=brand.voice_clone_status,
        email_template_style=brand.email_template_style,
        report_logo_placement=brand.report_logo_placement,
        meta_title=brand.meta_title,
        meta_description=brand.meta_description,
        keywords=brand.keywords,
        google_analytics_id=brand.google_analytics_id,
        facebook_pixel_id=brand.facebook_pixel_id,
        created_at=brand.created_at,
        updated_at=brand.updated_at,
        voice_summary=voice_summary,
    )


def _validate_file_extension(file: UploadFile, allowed: set, label: str):
    """Raise 400 if the uploaded file extension is not in the allowed set."""
    ext = Path(file.filename).suffix.lower() if file.filename else ""
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {label} file type '{ext}'. Allowed: {', '.join(sorted(allowed))}",
        )


async def _save_upload(
    file: UploadFile,
    subdir: str,
    custom_filename: str,
    old_url: Optional[str] = None,
) -> str:
    """Validate extension is present, delete old file if exists, save new file."""
    if old_url:
        file_storage.delete_file(old_url)
    return await file_storage.save_file(file=file, subdir=subdir, custom_filename=custom_filename)


def _get_or_create_brand(db: Session, agent_id: int) -> AgentBrand:
    """Get existing brand or create a new one. Raises 404 if agent doesn't exist."""
    brand = get_agent_brand(db, agent_id)
    if not brand:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        brand = AgentBrand(agent_id=agent_id)
        db.add(brand)
    return brand


# --- Background voice cloning ---

async def _clone_voice_background(agent_id: int, agent_name: str, file_path: str):
    """Background task: create ElevenLabs voice clone from uploaded sample."""
    pvc = PVCService(api_key=settings.elevenlabs_api_key)
    try:
        result = await pvc.create_pvc_voice(
            name=f"{agent_name} - Agent {agent_id}",
            description=f"Voice clone for agent {agent_name}",
        )
        voice_id = result["voice_id"]
        logger.info(f"Created PVC voice {voice_id} for agent {agent_id}")

        # Resolve the local file path from the URL path
        relative = file_path.removeprefix("/uploads/")
        abs_path = str(Path(file_storage.base_upload_dir) / relative)

        upload_result = await pvc.upload_pvc_samples(
            voice_id=voice_id,
            file_paths=[abs_path],
        )
        logger.info(f"Uploaded sample for voice {voice_id}: {upload_result.get('upload_count')} files")

        db = SessionLocal()
        try:
            brand = db.query(AgentBrand).filter(AgentBrand.agent_id == agent_id).first()
            if brand:
                brand.voice_clone_id = voice_id
                brand.voice_clone_status = "processing"
                db.commit()
        finally:
            db.close()

        # Poll until ready/failed (every 2 min, up to 6 hours)
        await _poll_voice_clone_status(agent_id, voice_id)

    except Exception as e:
        logger.error(f"Voice cloning failed for agent {agent_id}: {e}")
        db = SessionLocal()
        try:
            brand = db.query(AgentBrand).filter(AgentBrand.agent_id == agent_id).first()
            if brand:
                brand.voice_clone_status = "failed"
                db.commit()
        finally:
            db.close()
    finally:
        await pvc.close()


async def _poll_voice_clone_status(agent_id: int, voice_id: str):
    """Background task: poll ElevenLabs until voice clone is ready or failed."""
    pvc = PVCService(api_key=settings.elevenlabs_api_key)
    try:
        # Poll every 2 minutes, up to 6 hours
        for i in range(180):
            await asyncio.sleep(120)
            try:
                status_result = await pvc.get_pvc_status(voice_id)
                status = status_result.get("status", "").lower()
                logger.info(f"Voice clone {voice_id} poll #{i+1}: {status}")

                if status in ("ready", "failed"):
                    db = SessionLocal()
                    try:
                        brand = db.query(AgentBrand).filter(AgentBrand.agent_id == agent_id).first()
                        if brand:
                            brand.voice_clone_status = status
                            db.commit()
                    finally:
                        db.close()
                    logger.info(f"Voice clone {voice_id} finished: {status}")
                    return
            except Exception as e:
                logger.warning(f"Error polling voice clone {voice_id}: {e}")
    finally:
        await pvc.close()


# --- Endpoints ---

# Static routes MUST come before /{agent_id} parameterized routes

@router.get("/shotstack/templates")
def list_shotstack_templates():
    """List all saved Shotstack templates."""
    shotstack = ShotstackService()
    try:
        return shotstack.list_templates()
    finally:
        shotstack.close()


@router.get("/shotstack/templates/{template_id}")
def get_shotstack_template(template_id: str):
    """Get a Shotstack template by ID (returns full Edit JSON).

    Calls Shotstack REST API directly because the SDK loses polymorphic
    asset types when deserializing template responses.
    """
    import httpx

    stage = settings.shotstack_stage
    host = "https://api.shotstack.io/stage" if stage else "https://api.shotstack.io/v1"
    resp = httpx.get(
        f"{host}/templates/{template_id}",
        headers={"x-api-key": settings.shotstack_api_key},
        timeout=15.0,
    )
    resp.raise_for_status()
    return resp.json().get("response", {})


class SaveTemplateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    edit: Dict[str, Any]


@router.post("/shotstack/templates")
def save_shotstack_template(body: SaveTemplateRequest):
    """Save current edit JSON as a reusable Shotstack template."""
    from shotstack_sdk.model.edit import Edit as ShotstackEdit
    shotstack = ShotstackService()
    try:
        # Build an Edit from the raw dict by submitting through the SDK's deserializer
        api_client = shotstack._api_client
        edit_obj = api_client._ApiClient__deserialize(body.edit, 'Edit')
        template_id = shotstack.save_template(body.name, edit_obj)
        return {"id": template_id, "name": body.name}
    except Exception as e:
        logger.error(f"Failed to save template: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        shotstack.close()


@router.post("/{agent_id}", response_model=AgentBrandResponse)
def create_agent_brand(
    agent_id: int,
    brand_data: AgentBrandCreate,
    db: Session = Depends(get_db)
):
    """Create or update agent brand profile"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    existing_brand = get_agent_brand(db, agent_id)
    if existing_brand:
        raise HTTPException(status_code=400, detail="Brand profile already exists. Use PUT to update.")

    brand_data_dict = brand_data.model_dump(exclude_unset=True)
    brand = AgentBrand(agent_id=agent_id, **brand_data_dict)
    db.add(brand)
    db.commit()
    db.refresh(brand)

    voice_summary = f"Brand profile created for {agent.name}. {brand.company_name or 'Personal brand'} is now active."
    return _brand_to_response(brand, voice_summary)


@router.get("/{agent_id}", response_model=AgentBrandResponse)
def get_agent_brand_endpoint(
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Get agent brand profile"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    brand = get_agent_brand(db, agent_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand profile not found")

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

    return _brand_to_response(brand, voice_summary)


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

    update_data = brand_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(brand, field, value)

    db.commit()
    db.refresh(brand)

    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    voice_summary = f"{agent.name}'s brand profile updated successfully."
    return _brand_to_response(brand, voice_summary)


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

    colors = {
        'primary_color': primary_color,
        'secondary_color': secondary_color,
        'accent_color': accent_color,
        'background_color': background_color,
        'text_color': text_color
    }

    for field, value in colors.items():
        if value:
            if not value.startswith('#') or len(value) != 7:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid {field}: must be hex color (e.g., #FF5733)"
                )
            setattr(brand, field, value)

    db.commit()
    db.refresh(brand)

    voice_summary = f"Brand colors updated for {brand.company_name or 'your profile'}."
    return _brand_to_response(brand, voice_summary)


@router.post("/{agent_id}/logo", response_model=AgentBrandResponse)
async def upload_logo(
    agent_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload brand logo"""
    _validate_file_extension(file, ALLOWED_IMAGE_EXTENSIONS, "logo")
    brand = _get_or_create_brand(db, agent_id)

    logo_filename = f"logo_agent_{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    brand.logo_url = await _save_upload(file, "logos", logo_filename, old_url=brand.logo_url)

    db.commit()
    db.refresh(brand)

    voice_summary = f"Logo uploaded for {brand.company_name or 'your profile'}."
    return _brand_to_response(brand, voice_summary)


@router.post("/{agent_id}/headshot", response_model=AgentBrandResponse)
async def upload_headshot(
    agent_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload agent headshot photo"""
    _validate_file_extension(file, ALLOWED_IMAGE_EXTENSIONS, "headshot")
    brand = _get_or_create_brand(db, agent_id)

    headshot_filename = f"headshot_agent_{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    brand.headshot_url = await _save_upload(file, "headshots", headshot_filename, old_url=brand.headshot_url)

    db.commit()
    db.refresh(brand)

    voice_summary = f"Headshot uploaded for {brand.company_name or 'your profile'}."
    return _brand_to_response(brand, voice_summary)


@router.post("/{agent_id}/voice-sample", response_model=AgentBrandResponse)
async def upload_voice_sample(
    agent_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload agent voice sample and trigger ElevenLabs voice cloning"""
    _validate_file_extension(file, ALLOWED_AUDIO_EXTENSIONS, "voice sample")

    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    brand = _get_or_create_brand(db, agent_id)

    voice_filename = f"voice_agent_{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    brand.voice_sample_url = await _save_upload(file, "voice-samples", voice_filename, old_url=brand.voice_sample_url)
    brand.voice_clone_status = "pending"

    db.commit()
    db.refresh(brand)

    # Kick off voice cloning, then polling, as separate background tasks
    background_tasks.add_task(_clone_voice_background, agent_id, agent.name, brand.voice_sample_url)

    voice_summary = f"Voice sample uploaded for {brand.company_name or 'your profile'}. Voice cloning started in background."
    return _brand_to_response(brand, voice_summary)


@router.get("/{agent_id}/voice-clone-status")
async def get_voice_clone_status(
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Check ElevenLabs voice clone status on-demand and update DB"""
    brand = get_agent_brand(db, agent_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand profile not found")
    if not brand.voice_clone_id:
        return {
            "agent_id": agent_id,
            "voice_clone_id": None,
            "status": brand.voice_clone_status or "no_clone",
            "details": None,
        }

    pvc = PVCService(api_key=settings.elevenlabs_api_key)
    try:
        status_result = await pvc.get_pvc_status(brand.voice_clone_id)
        live_status = status_result.get("status", "unknown").lower()

        if live_status != brand.voice_clone_status:
            brand.voice_clone_status = live_status
            db.commit()
            db.refresh(brand)

        return {
            "agent_id": agent_id,
            "voice_clone_id": brand.voice_clone_id,
            "status": live_status,
            "details": status_result,
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to check ElevenLabs status: {str(e)}")
    finally:
        await pvc.close()


# --- Talking Head Video ---

class TalkingHeadRequest(BaseModel):
    script: str = Field(..., min_length=10, max_length=5000)


@router.post("/{agent_id}/talking-head-video", status_code=202)
async def create_talking_head_video(
    agent_id: int,
    request: TalkingHeadRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Generate a branded talking head video using HeyGen + agent's cloned voice and logo."""
    brand = get_agent_brand(db, agent_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand profile not found")
    if not brand.headshot_url:
        raise HTTPException(status_code=400, detail="Agent headshot required. Upload via POST /{agent_id}/headshot")
    if not brand.voice_clone_id or brand.voice_clone_status != "ready":
        raise HTTPException(status_code=400, detail="Voice clone must be ready. Upload a voice sample first.")

    job = TalkingHeadVideo(
        agent_id=agent_id,
        script=request.script,
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(generate_talking_head_video, job.id, agent_id, request.script)

    return {
        "video_id": job.id,
        "status": "pending",
        "message": "Video generation started. Poll the status endpoint for updates.",
    }


@router.get("/{agent_id}/talking-head-video/{video_id}")
def get_talking_head_video_status(
    agent_id: int,
    video_id: int,
    db: Session = Depends(get_db),
):
    """Check status of a talking head video generation job."""
    job = (
        db.query(TalkingHeadVideo)
        .filter(TalkingHeadVideo.id == video_id, TalkingHeadVideo.agent_id == agent_id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Video not found")

    return {
        "video_id": job.id,
        "agent_id": job.agent_id,
        "status": job.status,
        "video_url": job.video_url,
        "duration": job.duration,
        "error": job.error,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }


@router.get("/{agent_id}/talking-head-videos")
def list_talking_head_videos(
    agent_id: int,
    db: Session = Depends(get_db),
):
    """List all talking head videos for an agent."""
    jobs = (
        db.query(TalkingHeadVideo)
        .filter(TalkingHeadVideo.agent_id == agent_id)
        .order_by(TalkingHeadVideo.created_at.desc())
        .all()
    )
    return [
        {
            "video_id": j.id,
            "status": j.status,
            "video_url": j.video_url,
            "duration": j.duration,
            "created_at": j.created_at,
        }
        for j in jobs
    ]


# --- Property Video (Shotstack Pipeline) ---


class PropertyVideoRequest(BaseModel):
    video_search_queries: Optional[ListType[str]] = Field(
        None,
        description="Custom Pexels search queries for stock footage (up to 5). Auto-generated from property data if omitted.",
        max_length=5,
    )
    style: str = Field(
        "luxury",
        description="Video style: luxury, friendly, or professional",
        pattern=r'^(luxury|friendly|professional)$',
    )


@router.post("/{agent_id}/property-video/{property_id}", status_code=202)
async def create_property_video(
    agent_id: int,
    property_id: int,
    background_tasks: BackgroundTasks,
    body: Optional[PropertyVideoRequest] = None,
    db: Session = Depends(get_db),
):
    """Generate a branded property showcase video via Shotstack with talking heads, stock footage, and voiceover."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    brand = get_agent_brand(db, agent_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand profile not found")
    if not brand.voice_clone_id or brand.voice_clone_status != "ready":
        raise HTTPException(status_code=400, detail="Voice clone must be ready. Upload a voice sample first.")
    if not brand.headshot_url:
        raise HTTPException(status_code=400, detail="Agent headshot required. Upload via POST /{agent_id}/headshot")

    prop = db.query(Property).filter(Property.id == property_id, Property.agent_id == agent_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found or does not belong to this agent")

    style = body.style if body else "luxury"
    custom_queries = body.video_search_queries if body and body.video_search_queries else None

    job = PropertyVideoJob(
        agent_id=agent_id,
        property_id=property_id,
        style=style,
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(
        run_property_video_pipeline,
        job.id, agent_id, property_id, style, custom_queries,
    )

    return {
        "job_id": job.id,
        "status": "pending",
        "message": "Video generation started. Poll the status endpoint for updates.",
    }


@router.get("/{agent_id}/property-video/{job_id}/status")
async def get_property_video_status(
    agent_id: int,
    job_id: int,
    db: Session = Depends(get_db),
):
    """Check status of a property video generation job. Polls Shotstack live if rendering."""
    job = (
        db.query(PropertyVideoJob)
        .filter(PropertyVideoJob.id == job_id, PropertyVideoJob.agent_id == agent_id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Video job not found")

    # If still rendering, poll Shotstack for live status
    if job.status == "rendering" and job.shotstack_render_id:
        shotstack = ShotstackService()
        try:
            render = shotstack.get_render_status(job.shotstack_render_id)
            ss_status = render.get("status", "")
            if ss_status == "done":
                job.status = "done"
                job.video_url = render.get("url")
                db.commit()
                db.refresh(job)
            elif ss_status == "failed":
                job.status = "failed"
                job.error = "Shotstack render failed"
                db.commit()
                db.refresh(job)
        except Exception as e:
            logger.warning(f"Failed to poll Shotstack for job {job_id}: {e}")
        finally:
            shotstack.close()

    return {
        "job_id": job.id,
        "agent_id": job.agent_id,
        "property_id": job.property_id,
        "status": job.status,
        "video_url": job.video_url,
        "duration": job.duration,
        "style": job.style,
        "error": job.error,
        "stock_videos_used": job.stock_videos_used,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }


@router.get("/{agent_id}/property-video/{job_id}/timeline")
async def get_property_video_timeline(
    agent_id: int,
    job_id: int,
    db: Session = Depends(get_db),
):
    """Return the stored Shotstack Edit JSON for a property/brand video job."""
    job = (
        db.query(PropertyVideoJob)
        .filter(PropertyVideoJob.id == job_id, PropertyVideoJob.agent_id == agent_id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Video job not found")
    if not job.timeline_json:
        raise HTTPException(status_code=404, detail="No timeline stored for this job")

    return job.timeline_json


# --- Brand Video (2 min: logo intro → HeyGen talking head) ---


class BrandVideoRequest(BaseModel):
    script: str = Field(..., min_length=10, max_length=10000, description="The script for the talking head to speak")
    enhance_script: bool = Field(True, description="AI-enhance the script for voiceover delivery before TTS")
    style: str = Field("professional", description="Script style: luxury, friendly, or professional", pattern=r'^(luxury|friendly|professional)$')
    background_music_url: Optional[str] = Field(None, description="Optional URL to background music MP3")


@router.post("/{agent_id}/brand-video", status_code=202)
async def create_brand_video(
    agent_id: int,
    request: BrandVideoRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Generate a ~2 min brand video: 4s logo intro → HeyGen talking head with cloned voice."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    brand = get_agent_brand(db, agent_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand profile not found")
    if not brand.voice_clone_id or brand.voice_clone_status != "ready":
        raise HTTPException(status_code=400, detail="Voice clone must be ready. Upload a voice sample first.")
    if not brand.headshot_url:
        raise HTTPException(status_code=400, detail="Agent headshot required.")
    if not brand.logo_url:
        raise HTTPException(status_code=400, detail="Logo required. Upload via POST /{agent_id}/logo")

    job = PropertyVideoJob(
        agent_id=agent_id,
        property_id=0,  # No property — this is a brand video
        style="brand",
        script=request.script,
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(
        run_brand_video_pipeline,
        job.id, agent_id, request.script,
        request.background_music_url,
        request.enhance_script, request.style,
    )

    return {
        "job_id": job.id,
        "status": "pending",
        "message": "Brand video generation started. Poll the status endpoint for updates.",
    }


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
    return _brand_to_response(brand, voice_summary)
