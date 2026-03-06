"""Property Video Pipeline Service

Orchestrates the full video generation pipeline:
  1. Load brand + property data
  2. Generate voiceover script (OpenRouter / Claude)
  3. Generate TTS audio (ElevenLabs cloned voice)
  4. Upload TTS to S3 for public URL
  5. Generate HeyGen talking-head intro + outro (parallel)
  6. Fetch Pexels stock footage
  7. Extract Zillow photos
  8. Build Shotstack timeline → submit render
"""
import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

import boto3
import httpx
from botocore.exceptions import ClientError

from app.config import settings
from app.database import SessionLocal
from app.models.agent import Agent
from app.models.agent_brand import AgentBrand
from app.models.property import Property
from app.models.property_video_job import PropertyVideoJob
from app.services.heygen_enhanced_service import HeyGenEnhancedService
from app.services.pexels_service import PexelsService
from app.services.script_generator_enhanced import ScriptGeneratorService
from app.services.shotstack_service import ShotstackService

logger = logging.getLogger(__name__)

TEMP_DIR = Path(tempfile.gettempdir()) / "video_pipeline"
TEMP_DIR.mkdir(exist_ok=True)

# S3 client (lazy — only used if credentials are configured)
_s3_client = None


def _get_s3_client():
    global _s3_client
    if _s3_client is None and settings.aws_access_key_id:
        _s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
        )
    return _s3_client


def _update_job(job_id: int, **kwargs):
    """Update a PropertyVideoJob record (short-lived session)."""
    db = SessionLocal()
    try:
        job = db.query(PropertyVideoJob).filter(PropertyVideoJob.id == job_id).first()
        if job:
            for k, v in kwargs.items():
                setattr(job, k, v)
            db.commit()
    finally:
        db.close()


async def _generate_elevenlabs_tts(script: str, voice_id: str, output_path: Path) -> Path:
    """Generate TTS audio via ElevenLabs API (same pattern as talking_head_service)."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": settings.elevenlabs_api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": script,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True,
        },
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        output_path.write_bytes(resp.content)
    logger.info(f"ElevenLabs TTS generated: {output_path} ({output_path.stat().st_size} bytes)")
    return output_path


async def _upload_to_s3(local_path: Path, s3_key: str, content_type: str = "audio/mpeg") -> str:
    """Upload a file to S3 and return a public URL (presigned, 24h)."""
    s3 = _get_s3_client()
    if not s3:
        raise RuntimeError("AWS S3 credentials not configured")
    bucket = settings.aws_s3_bucket
    s3.upload_file(str(local_path), bucket, s3_key, ExtraArgs={"ContentType": content_type})
    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": s3_key},
        ExpiresIn=86400,
    )
    logger.info(f"Uploaded to S3: s3://{bucket}/{s3_key}")
    return url


async def _generate_heygen_talking_head(
    heygen: HeyGenEnhancedService,
    avatar_id: str,
    script: str,
    voice_clone_id: str,
    label: str,
    job_id: int,
) -> str:
    """Generate a single talking-head clip via HeyGen and return its video URL."""
    # TTS for this segment
    tts_path = TEMP_DIR / f"tts_{label}_{job_id}.mp3"
    await _generate_elevenlabs_tts(script, voice_clone_id, tts_path)

    # Upload audio to HeyGen
    audio_asset_id = await heygen.upload_audio_asset(str(tts_path))
    logger.info(f"[{label}] Audio uploaded to HeyGen: {audio_asset_id}")

    # Generate talking head
    gen_result = await heygen.generate_talking_head(
        avatar_id=avatar_id,
        script=script,
        audio_asset_id=audio_asset_id,
    )
    video_id = gen_result["video_id"]
    logger.info(f"[{label}] HeyGen video started: {video_id}")

    # Wait for completion
    video_data = await heygen.wait_for_video(video_id, timeout=900)
    video_url = video_data.get("video_url")
    if not video_url:
        raise RuntimeError(f"HeyGen returned no video URL for {label}")
    logger.info(f"[{label}] HeyGen video ready: {video_url}")
    return video_url


async def run_property_video_pipeline(
    job_id: int,
    agent_id: int,
    property_id: int,
    style: str = "luxury",
    custom_queries: Optional[List[str]] = None,
):
    """Background task: full property video pipeline.

    Status progression:
      pending → loading_data → generating_script → generating_tts →
      uploading_audio → generating_talking_heads → fetching_stock_footage →
      building_timeline → rendering → done / failed
    """
    heygen = HeyGenEnhancedService()
    shotstack = ShotstackService()

    try:
        # ── 1. Load data ──────────────────────────────────────
        _update_job(job_id, status="loading_data")
        db = SessionLocal()
        try:
            brand = db.query(AgentBrand).filter(AgentBrand.agent_id == agent_id).first()
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            prop = db.query(Property).filter(Property.id == property_id).first()
            zillow = getattr(prop, "zillow_enrichment", None) if prop else None

            if not brand or not agent or not prop:
                raise ValueError("Missing brand, agent, or property data")

            # Extract to plain dicts before closing session
            brand_data = {
                "voice_clone_id": brand.voice_clone_id,
                "heygen_avatar_id": brand.heygen_avatar_id,
                "logo_url": brand.logo_url,
                "company_name": brand.company_name or "",
                "primary_color": brand.primary_color or "#1E3A8A",
                "text_color": brand.text_color or "#FFFFFF",
                "headshot_url": brand.headshot_url,
            }
            agent_data = {
                "name": agent.name,
                "phone": brand.display_phone or "",
                "email": brand.display_email or "",
            }
            prop_data = {
                "address": prop.address,
                "city": prop.city,
                "state": prop.state,
                "price": prop.price,
                "bedrooms": prop.bedrooms,
                "bathrooms": prop.bathrooms,
                "square_feet": prop.square_feet,
                "description": prop.description or "",
                "property_type": str(prop.property_type.value) if prop.property_type else "house",
            }
            zillow_photos = (zillow.photos or [])[:5] if zillow else []
        finally:
            db.close()

        avatar_id = brand_data["heygen_avatar_id"]
        voice_clone_id = brand_data["voice_clone_id"]
        if not avatar_id:
            raise ValueError("HeyGen avatar not configured. Generate a talking head video first to create the avatar.")

        # ── 2. Generate script ────────────────────────────────
        _update_job(job_id, status="generating_script")
        script_svc = ScriptGeneratorService()
        try:
            script_result = await script_svc.generate_property_script(
                property_data=prop_data,
                style=style,
                duration=70,
            )
        finally:
            await script_svc.client.aclose()

        intro_script = script_result.get("agent_intro", "")
        highlights_script = script_result.get("property_highlights", "")
        cta_script = script_result.get("call_to_action", "")
        full_script = f"{intro_script} {highlights_script} {cta_script}"

        _update_job(job_id, script=full_script)

        # ── 3. Generate full TTS audio ────────────────────────
        _update_job(job_id, status="generating_tts")
        full_tts_path = TEMP_DIR / f"full_tts_{job_id}.mp3"
        await _generate_elevenlabs_tts(full_script, voice_clone_id, full_tts_path)

        # ── 4. Upload TTS to S3 ──────────────────────────────
        _update_job(job_id, status="uploading_audio")
        voiceover_s3_key = f"video-pipeline/voiceover_{job_id}.mp3"
        voiceover_url = await _upload_to_s3(full_tts_path, voiceover_s3_key)

        # ── 5. Generate HeyGen talking heads (parallel) ───────
        _update_job(job_id, status="generating_talking_heads")

        intro_task = _generate_heygen_talking_head(
            heygen, avatar_id, intro_script, voice_clone_id, "intro", job_id,
        )
        outro_task = _generate_heygen_talking_head(
            heygen, avatar_id, cta_script, voice_clone_id, "outro", job_id,
        )
        intro_video_url, outro_video_url = await asyncio.gather(intro_task, outro_task)

        # ── 6. Fetch Pexels stock footage ─────────────────────
        _update_job(job_id, status="fetching_stock_footage")
        stock_video_urls: List[str] = []
        if settings.pexels_api_key:
            pexels = PexelsService()
            queries = custom_queries
            if not queries:
                queries = PexelsService.generate_search_queries(prop, zillow)
            try:
                stock_video_urls = await pexels.get_stock_videos(queries)
                logger.info(f"Fetched {len(stock_video_urls)} Pexels videos for job {job_id}")
            except Exception as e:
                logger.warning(f"Pexels fetch failed, continuing: {e}")

        # ── 7. Extract Zillow photos ──────────────────────────
        # Already extracted above as zillow_photos

        # ── 8. Build Shotstack timeline ───────────────────────
        _update_job(job_id, status="building_timeline")

        # Build detail lines for overlay text
        details_parts = []
        if prop_data.get("bedrooms"):
            details_parts.append(f"{prop_data['bedrooms']} Bed")
        if prop_data.get("bathrooms"):
            details_parts.append(f"{prop_data['bathrooms']} Bath")
        if prop_data.get("square_feet"):
            details_parts.append(f"{prop_data['square_feet']:,} sqft")
        if prop_data.get("price"):
            details_parts.append(f"${prop_data['price']:,.0f}")
        property_details = " | ".join(details_parts)

        edit = shotstack.build_property_timeline(
            intro_video_url=intro_video_url,
            outro_video_url=outro_video_url,
            stock_video_urls=stock_video_urls,
            zillow_photo_urls=zillow_photos,
            logo_url=brand_data.get("logo_url"),
            voiceover_url=voiceover_url,
            agent_name=agent_data["name"],
            agent_phone=agent_data["phone"],
            agent_email=agent_data["email"],
            address=prop_data["address"],
            property_details=property_details,
            primary_color=brand_data["primary_color"],
            text_color=brand_data["text_color"],
            style=style,
        )

        # ── 9. Submit to Shotstack ────────────────────────────
        _update_job(job_id, status="rendering", timeline_json=edit)
        render_result = shotstack.submit_render(edit)
        render_id = render_result["id"]
        _update_job(
            job_id,
            shotstack_render_id=render_id,
            stock_videos_used=stock_video_urls,
        )
        logger.info(f"Shotstack render submitted: {render_id} for job {job_id}")

        # Note: We don't poll here — the status endpoint polls on demand.
        # The job stays in "rendering" until the client polls and we detect done/failed.

    except Exception as e:
        logger.error(f"Property video pipeline failed for job {job_id}: {e}")
        _update_job(job_id, status="failed", error=str(e)[:500])
    finally:
        await heygen.close()
        shotstack.close()
        # Cleanup temp files for this job
        for p in TEMP_DIR.glob(f"*_{job_id}*"):
            p.unlink(missing_ok=True)


# ======================================================================
# Brand Video Pipeline: 4s logo intro → HeyGen talking head (~2 min)
# ======================================================================

async def run_brand_video_pipeline(
    job_id: int,
    agent_id: int,
    script: str,
    background_music_url: Optional[str] = None,
    enhance_script: bool = True,
    style: str = "professional",
):
    """Background task: generate a ~2 min brand video.

    Pipeline:
      1. Load brand data (logo, voice clone, avatar, colors)
      1b. (Optional) AI-enhance script for voiceover delivery
      2. Generate TTS audio via ElevenLabs (cloned voice)
      3. Upload audio to HeyGen → generate talking head → wait
      4. Build Shotstack timeline: [4s logo] → [talking head with audio]
      5. Submit render

    Status: pending → loading_data → enhancing_script → generating_tts →
            generating_talking_head → building_timeline → rendering → done/failed
    """
    heygen = HeyGenEnhancedService()
    shotstack = ShotstackService()

    try:
        # ── 1. Load brand data ────────────────────────────────
        _update_job(job_id, status="loading_data")
        db = SessionLocal()
        try:
            brand = db.query(AgentBrand).filter(AgentBrand.agent_id == agent_id).first()
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            if not brand or not agent:
                raise ValueError("Missing brand or agent data")

            brand_data = {
                "voice_clone_id": brand.voice_clone_id,
                "heygen_avatar_id": brand.heygen_avatar_id,
                "logo_url": brand.logo_url,
                "company_name": brand.company_name or "",
                "primary_color": brand.primary_color or "#1E3A8A",
                "text_color": brand.text_color or "#FFFFFF",
                "tagline": brand.tagline or "",
                "display_phone": brand.display_phone or "",
                "display_email": brand.display_email or "",
                "website_url": brand.website_url or "",
            }
            agent_name = agent.name
        finally:
            db.close()

        avatar_id = brand_data["heygen_avatar_id"]
        voice_clone_id = brand_data["voice_clone_id"]
        logo_url = brand_data["logo_url"]

        if not avatar_id:
            raise ValueError("HeyGen avatar not configured. Generate a talking head video first.")
        if not voice_clone_id:
            raise ValueError("Voice clone not configured. Upload a voice sample first.")
        if not logo_url:
            raise ValueError("Logo not uploaded. Upload via POST /{agent_id}/logo")

        # ── 1b. AI-enhance script for voiceover ──────────────
        if enhance_script:
            _update_job(job_id, status="enhancing_script")
            script_svc = ScriptGeneratorService()
            try:
                result = await script_svc.enhance_voiceover_script(
                    raw_script=script,
                    style=style,
                    agent_name=agent_name,
                    company_name=brand_data["company_name"],
                )
                script = result.get("enhanced_script", script)
                logger.info(f"[brand-video] Script enhanced: {result.get('changes_summary', '')}")
            except Exception as e:
                logger.warning(f"[brand-video] Script enhancement failed, using original: {e}")
            finally:
                await script_svc.client.aclose()

        _update_job(job_id, script=script)

        # ── 2. Generate TTS audio ────────────────────────────
        _update_job(job_id, status="generating_tts")
        tts_path = TEMP_DIR / f"brand_tts_{job_id}.mp3"
        await _generate_elevenlabs_tts(script, voice_clone_id, tts_path)

        # ── 3. Generate HeyGen talking head ───────────────────
        _update_job(job_id, status="generating_talking_head")

        # Upload audio to HeyGen
        audio_asset_id = await heygen.upload_audio_asset(str(tts_path))
        logger.info(f"[brand-video] Audio uploaded to HeyGen: {audio_asset_id}")

        # Generate talking head with lip-synced audio
        gen_result = await heygen.generate_talking_head(
            avatar_id=avatar_id,
            script=script,
            audio_asset_id=audio_asset_id,
        )
        heygen_video_id = gen_result["video_id"]
        logger.info(f"[brand-video] HeyGen video started: {heygen_video_id}")

        # Wait for HeyGen to finish (can take 10-15 min for 2 min video)
        video_data = await heygen.wait_for_video(heygen_video_id, timeout=900)
        heygen_video_url = video_data.get("video_url")
        heygen_duration = video_data.get("duration", 116)
        if not heygen_video_url:
            raise RuntimeError("HeyGen returned no video URL")
        logger.info(f"[brand-video] HeyGen video ready: {heygen_video_url} ({heygen_duration}s)")

        # ── 4. Build Shotstack timeline ───────────────────────
        _update_job(job_id, status="building_timeline")

        edit = shotstack.build_brand_video_timeline(
            logo_url=logo_url,
            heygen_video_url=heygen_video_url,
            heygen_video_duration=float(heygen_duration),
            logo_intro_length=4.0,
            cta_outro_length=6.0,
            primary_color=brand_data["primary_color"],
            text_color=brand_data["text_color"],
            agent_name=agent_name,
            company_name=brand_data["company_name"],
            agent_phone=brand_data["display_phone"],
            agent_email=brand_data["display_email"],
            website_url=brand_data["website_url"],
            tagline=brand_data["tagline"],
            background_music_url=background_music_url,
        )

        # ── 5. Submit to Shotstack ────────────────────────────
        _update_job(job_id, status="rendering", timeline_json=edit)
        render_result = shotstack.submit_render(edit)
        render_id = render_result["id"]
        _update_job(
            job_id,
            shotstack_render_id=render_id,
            duration=heygen_duration + 4 + 6,  # intro + talking head + CTA outro
        )
        logger.info(f"[brand-video] Shotstack render submitted: {render_id} for job {job_id}")

    except Exception as e:
        logger.error(f"Brand video pipeline failed for job {job_id}: {e}")
        _update_job(job_id, status="failed", error=str(e)[:500])
    finally:
        await heygen.close()
        shotstack.close()
        for p in TEMP_DIR.glob(f"*_{job_id}*"):
            p.unlink(missing_ok=True)
