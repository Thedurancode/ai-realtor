"""Shotstack Create API Router — Generative AI Assets + Consolidated Pipeline

Endpoints:
  POST /shotstack/create/tts           — Text-to-speech (Shotstack native or ElevenLabs)
  POST /shotstack/create/avatar        — Text-to-avatar (HeyGen or D-ID)
  POST /shotstack/create/image         — Text-to-image (Stability AI or Shotstack)
  GET  /shotstack/create/asset/{id}    — Poll asset status
  GET  /shotstack/create/voices        — List available TTS voices
  GET  /shotstack/create/avatars       — List available avatar IDs
  GET  /shotstack/create/styles        — List Stability AI style presets
  POST /shotstack/create/pipeline/property  — Consolidated property video
  POST /shotstack/create/pipeline/brand     — Consolidated brand video
"""
import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.property_video_job import PropertyVideoJob
from app.services.shotstack_create_service import (
    ShotstackCreateService,
    HEYGEN_STOCK_AVATARS,
    SHOTSTACK_VOICES,
    STABILITY_STYLES,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/shotstack/create", tags=["Shotstack Create AI"])


# ── Request/Response schemas ──────────────────────────────────────────

class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Text to convert to speech")
    voice: str = Field("matthew", description="Voice ID or name")
    provider: str = Field("shotstack", description="Provider: shotstack or elevenlabs")

class AvatarRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Script for avatar to speak")
    avatar: str = Field("anna_commercial", description="Avatar ID")
    voice: Optional[str] = Field(None, description="Voice override (provider default if omitted)")
    provider: str = Field("heygen", description="Provider: heygen or d-id")
    background: str = Field("#00FF00", description="Background color (green for chroma key)")
    ratio: str = Field("16:9", description="Aspect ratio: 16:9, 9:16, 1:1")
    test: bool = Field(False, description="Use HeyGen test mode (low quality, free)")

class ImageRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000, description="Image generation prompt")
    width: int = Field(1024, ge=256, le=2048)
    height: int = Field(576, ge=256, le=2048)
    provider: str = Field("stability-ai", description="Provider: stability-ai or shotstack")
    style_preset: str = Field("photographic", description="Stability AI style preset")

class AssetResponse(BaseModel):
    id: str
    status: str
    url: Optional[str] = None
    provider: Optional[str] = None
    type: Optional[str] = None

class ConsolidatedPropertyRequest(BaseModel):
    agent_id: int
    property_id: int
    style: str = Field("luxury", description="Style: luxury, friendly, professional")
    tts_provider: str = Field("shotstack", description="TTS provider: shotstack or elevenlabs")
    tts_voice: str = Field("matthew", description="TTS voice name/ID")
    avatar_provider: str = Field("heygen", description="Avatar provider: heygen or d-id")
    avatar_id: str = Field("anna_commercial", description="Avatar ID")
    avatar_voice: Optional[str] = Field(None, description="Avatar voice override")
    generate_ai_backgrounds: bool = Field(False, description="Generate AI scene backgrounds")
    background_music_url: Optional[str] = None
    custom_search_queries: Optional[List[str]] = Field(None, description="Custom Pexels search queries")

class ConsolidatedBrandRequest(BaseModel):
    agent_id: int
    script: str = Field(..., min_length=10, max_length=10000)
    style: str = Field("professional")
    tts_provider: str = Field("shotstack")
    tts_voice: str = Field("matthew")
    avatar_provider: str = Field("heygen")
    avatar_id: str = Field("anna_commercial")
    avatar_voice: Optional[str] = None
    background_music_url: Optional[str] = None
    enhance_script: bool = Field(True, description="AI-enhance the script before generation")


# ── Endpoints ─────────────────────────────────────────────────────────

@router.post("/tts", response_model=AssetResponse)
def create_tts(req: TTSRequest):
    """Generate text-to-speech audio.

    Providers:
      - **shotstack**: Free with plan, 10+ voices, fast
      - **elevenlabs**: Premium quality, voice cloning support (requires EL key in Shotstack dashboard)
    """
    svc = ShotstackCreateService()
    try:
        if req.provider == "elevenlabs":
            asset_id = svc.create_tts_elevenlabs(text=req.text, voice=req.voice)
        else:
            asset_id = svc.create_tts_shotstack(text=req.text, voice=req.voice)
        return AssetResponse(id=asset_id, status="queued")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        svc.close()


@router.post("/avatar", response_model=AssetResponse)
def create_avatar(req: AvatarRequest):
    """Generate a talking-head avatar video.

    Providers:
      - **heygen**: 24 stock avatars, lip-synced speech, green screen support
      - **d-id**: Alternative avatar provider
    """
    svc = ShotstackCreateService()
    try:
        if req.provider == "d-id":
            asset_id = svc.create_avatar_did(
                text=req.text, avatar=req.avatar, background=req.background,
            )
        else:
            asset_id = svc.create_avatar_heygen(
                text=req.text, avatar=req.avatar, voice=req.voice,
                background=req.background, ratio=req.ratio, test=req.test,
            )
        return AssetResponse(id=asset_id, status="queued")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        svc.close()


@router.post("/image", response_model=AssetResponse)
def create_image(req: ImageRequest):
    """Generate an AI image from a text prompt.

    Providers:
      - **stability-ai**: Stable Diffusion XL, multiple style presets
      - **shotstack**: Native image generation
    """
    svc = ShotstackCreateService()
    try:
        if req.provider == "shotstack":
            asset_id = svc.create_image_shotstack(
                prompt=req.prompt, width=req.width, height=req.height,
            )
        else:
            asset_id = svc.create_image_stability(
                prompt=req.prompt, width=req.width, height=req.height,
                style_preset=req.style_preset,
            )
        return AssetResponse(id=asset_id, status="queued")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        svc.close()


@router.get("/asset/{asset_id}", response_model=AssetResponse)
def get_asset_status(asset_id: str):
    """Poll the status of a generated asset.

    Status flow: queued → processing → done / failed
    When done, the `url` field contains the hosted asset URL.
    """
    svc = ShotstackCreateService()
    try:
        result = svc.get_asset_status(asset_id)
        return AssetResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        svc.close()


@router.get("/voices")
def list_voices():
    """List available TTS voices by provider."""
    return {
        "shotstack": SHOTSTACK_VOICES,
        "elevenlabs": "Use your ElevenLabs voice IDs (configure in Shotstack dashboard → Integrations)",
    }


@router.get("/avatars")
def list_avatars():
    """List available avatar IDs by provider."""
    return {
        "heygen": HEYGEN_STOCK_AVATARS,
        "d-id": ["amy", "anna", "lottie", "emma", "sara"],
    }


@router.get("/styles")
def list_image_styles():
    """List available Stability AI style presets."""
    return {"stability_ai_presets": STABILITY_STYLES}


@router.post("/pipeline/property")
async def consolidated_property_video(
    req: ConsolidatedPropertyRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Launch a property video using the consolidated Shotstack-only pipeline.

    This replaces the legacy 3-API pipeline (ElevenLabs + HeyGen + Shotstack)
    with a single Shotstack API flow:
      1. Shotstack Create API generates TTS audio + avatar videos (parallel)
      2. Optional: Stability AI generates scene backgrounds
      3. Shotstack Edit API composites everything into final video

    **Advantages**: 1 API key, no S3 uploads, ~50% faster, unified billing.
    """
    from app.services.video_pipeline_consolidated import run_consolidated_property_video

    # Create job record
    job = PropertyVideoJob(
        agent_id=req.agent_id,
        property_id=req.property_id,
        status="pending",
        pipeline_type="consolidated",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(
        run_consolidated_property_video,
        job_id=job.id,
        agent_id=req.agent_id,
        property_id=req.property_id,
        style=req.style,
        custom_queries=req.custom_search_queries,
        tts_provider=req.tts_provider,
        tts_voice=req.tts_voice,
        avatar_provider=req.avatar_provider,
        avatar_id=req.avatar_id,
        avatar_voice=req.avatar_voice,
        generate_ai_backgrounds=req.generate_ai_backgrounds,
        background_music_url=req.background_music_url,
    )

    return {
        "job_id": job.id,
        "status": "pending",
        "pipeline": "consolidated",
        "message": "Property video generation started (Shotstack-only pipeline)",
    }


@router.post("/pipeline/brand")
async def consolidated_brand_video(
    req: ConsolidatedBrandRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Launch a brand video using the consolidated Shotstack-only pipeline.

    Single API call generates avatar with lip-synced speech, then composites
    with logo intro/outro via Shotstack Edit API.
    """
    from app.services.video_pipeline_consolidated import run_consolidated_brand_video

    job = PropertyVideoJob(
        agent_id=req.agent_id,
        status="pending",
        script=req.script,
        pipeline_type="consolidated",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(
        run_consolidated_brand_video,
        job_id=job.id,
        agent_id=req.agent_id,
        script=req.script,
        tts_provider=req.tts_provider,
        tts_voice=req.tts_voice,
        avatar_provider=req.avatar_provider,
        avatar_id=req.avatar_id,
        avatar_voice=req.avatar_voice,
        background_music_url=req.background_music_url,
        enhance_script=req.enhance_script,
        style=req.style,
    )

    return {
        "job_id": job.id,
        "status": "pending",
        "pipeline": "consolidated",
        "message": "Brand video generation started (Shotstack-only pipeline)",
    }
