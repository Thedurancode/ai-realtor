"""Consolidated Video Pipeline — Single Shotstack API

Replaces the 3-API pipeline (ElevenLabs + HeyGen + Shotstack Edit)
with a unified flow that uses Shotstack Create API for TTS and avatars,
then Shotstack Edit API for final rendering.

Benefits:
  - 1 API key instead of 3
  - No S3 intermediary for audio
  - ~30s latency vs ~60s (no cross-service transfers)
  - Unified error handling and billing

Pipeline:
  1. Load brand + property data
  2. Generate voiceover script (OpenRouter / Claude)
  3. Shotstack Create API: text-to-speech → hosted audio URL
  4. Shotstack Create API: text-to-avatar → hosted avatar video URL (with lip-sync)
  5. Optional: Shotstack Create API: text-to-image → AI-generated scene backgrounds
  6. Fetch Pexels stock footage (optional fallback)
  7. Build Shotstack Edit timeline → submit render
"""
import asyncio
import logging
from typing import Dict, List, Optional

from app.config import settings
from app.database import SessionLocal
from app.models.agent import Agent
from app.models.agent_brand import AgentBrand
from app.models.property import Property
from app.models.property_video_job import PropertyVideoJob
from app.services.pexels_service import PexelsService
from app.services.script_generator_enhanced import ScriptGeneratorService
from app.services.shotstack_service import ShotstackService
from app.services.shotstack_create_service import ShotstackCreateService

logger = logging.getLogger(__name__)


def _update_job(job_id: int, **kwargs):
    """Update a PropertyVideoJob record."""
    db = SessionLocal()
    try:
        job = db.query(PropertyVideoJob).filter(PropertyVideoJob.id == job_id).first()
        if job:
            for k, v in kwargs.items():
                setattr(job, k, v)
            db.commit()
    finally:
        db.close()


async def run_consolidated_property_video(
    job_id: int,
    agent_id: int,
    property_id: int,
    style: str = "luxury",
    custom_queries: Optional[List[str]] = None,
    tts_provider: str = "shotstack",
    tts_voice: str = "matthew",
    avatar_provider: str = "heygen",
    avatar_id: str = "anna_commercial",
    avatar_voice: Optional[str] = None,
    generate_ai_backgrounds: bool = False,
    background_music_url: Optional[str] = None,
):
    """Background task: consolidated property video pipeline.

    All TTS and avatar generation happens through Shotstack Create API.
    No ElevenLabs key, no HeyGen key, no S3 uploads needed.

    Status progression:
      pending → loading_data → generating_script → generating_assets →
      fetching_stock_footage → building_timeline → rendering → done / failed
    """
    create_svc = ShotstackCreateService()
    edit_svc = ShotstackService()

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

            brand_data = {
                "logo_url": brand.logo_url,
                "company_name": brand.company_name or "",
                "primary_color": brand.primary_color or "#1E3A8A",
                "text_color": brand.text_color or "#FFFFFF",
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

        # ── 2. Generate script ────────────────────────────────
        _update_job(job_id, status="generating_script")
        script_svc = ScriptGeneratorService()
        try:
            script_result = await script_svc.generate_property_script(
                property_data=prop_data, style=style, duration=70,
            )
        finally:
            await script_svc.client.aclose()

        intro_script = script_result.get("agent_intro", "")
        highlights_script = script_result.get("property_highlights", "")
        cta_script = script_result.get("call_to_action", "")
        full_script = f"{intro_script} {highlights_script} {cta_script}"
        _update_job(job_id, script=full_script)

        # ── 3. Generate assets via Shotstack Create API (parallel) ──
        _update_job(job_id, status="generating_assets")

        tasks = []

        # TTS for voiceover
        tts_task = create_svc.generate_tts(
            text=full_script, voice=tts_voice, provider=tts_provider, timeout=300,
        )
        tasks.append(("voiceover", tts_task))

        # Avatar for intro
        intro_avatar_task = create_svc.generate_avatar(
            text=intro_script, avatar=avatar_id, voice=avatar_voice,
            provider=avatar_provider, background="#00FF00", ratio="16:9", timeout=600,
        )
        tasks.append(("intro_avatar", intro_avatar_task))

        # Avatar for outro
        outro_avatar_task = create_svc.generate_avatar(
            text=cta_script, avatar=avatar_id, voice=avatar_voice,
            provider=avatar_provider, background="#00FF00", ratio="16:9", timeout=600,
        )
        tasks.append(("outro_avatar", outro_avatar_task))

        # Optional: AI-generated backgrounds
        ai_images: List[str] = []
        if generate_ai_backgrounds:
            prompts = [
                f"Luxury real estate interior, modern living room, {prop_data['property_type']}, photorealistic",
                f"Beautiful exterior of a {prop_data.get('bedrooms', 3)} bedroom home, landscaped yard, golden hour",
                f"Aerial view of {prop_data.get('city', 'suburban')} neighborhood, real estate photography",
            ]
            for prompt in prompts:
                img_task = create_svc.generate_image(
                    prompt=prompt, width=1920, height=1080,
                    style_preset="photographic", timeout=120,
                )
                tasks.append(("ai_image", img_task))

        # Run all in parallel
        task_names = [t[0] for t in tasks]
        task_coros = [t[1] for t in tasks]
        results = await asyncio.gather(*task_coros, return_exceptions=True)

        assets: Dict[str, str] = {}
        for name, result in zip(task_names, results):
            if isinstance(result, Exception):
                logger.error(f"Asset generation failed for {name}: {result}")
                if name in ("voiceover", "intro_avatar", "outro_avatar"):
                    raise result  # Critical assets
            elif name == "ai_image":
                ai_images.append(result)
            else:
                assets[name] = result

        voiceover_url = assets["voiceover"]
        intro_video_url = assets["intro_avatar"]
        outro_video_url = assets["outro_avatar"]

        logger.info(
            f"All assets generated. Voiceover: {voiceover_url}, "
            f"Intro: {intro_video_url}, Outro: {outro_video_url}, "
            f"AI images: {len(ai_images)}"
        )

        # ── 4. Fetch Pexels stock footage (optional) ──────────
        _update_job(job_id, status="fetching_stock_footage")
        stock_video_urls: List[str] = []
        if settings.pexels_api_key:
            pexels = PexelsService()
            queries = custom_queries or PexelsService.generate_search_queries(prop, zillow)
            try:
                stock_video_urls = await pexels.get_stock_videos(queries)
                logger.info(f"Fetched {len(stock_video_urls)} Pexels videos")
            except Exception as e:
                logger.warning(f"Pexels fetch failed, continuing: {e}")

        # Use AI-generated images as extra scene backgrounds
        all_photos = zillow_photos + ai_images

        # ── 5. Build Shotstack Edit timeline ──────────────────
        _update_job(job_id, status="building_timeline")

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

        edit = edit_svc.build_property_timeline(
            intro_video_url=intro_video_url,
            outro_video_url=outro_video_url,
            stock_video_urls=stock_video_urls,
            zillow_photo_urls=all_photos,
            logo_url=brand_data.get("logo_url"),
            voiceover_url=voiceover_url,
            background_music_url=background_music_url,
            agent_name=agent_data["name"],
            agent_phone=agent_data["phone"],
            agent_email=agent_data["email"],
            address=prop_data["address"],
            property_details=property_details,
            primary_color=brand_data["primary_color"],
            text_color=brand_data["text_color"],
            style=style,
        )

        # ── 6. Submit render ──────────────────────────────────
        _update_job(job_id, status="rendering", timeline_json=edit.to_dict())
        render_result = edit_svc.submit_render(edit)
        render_id = render_result["id"]
        _update_job(
            job_id,
            shotstack_render_id=render_id,
            stock_videos_used=stock_video_urls,
        )
        logger.info(f"Render submitted: {render_id} for job {job_id}")

    except Exception as e:
        logger.error(f"Consolidated pipeline failed for job {job_id}: {e}")
        _update_job(job_id, status="failed", error=str(e)[:500])
    finally:
        create_svc.close()
        edit_svc.close()


async def run_consolidated_brand_video(
    job_id: int,
    agent_id: int,
    script: str,
    tts_provider: str = "shotstack",
    tts_voice: str = "matthew",
    avatar_provider: str = "heygen",
    avatar_id: str = "anna_commercial",
    avatar_voice: Optional[str] = None,
    background_music_url: Optional[str] = None,
    enhance_script: bool = True,
    style: str = "professional",
):
    """Background task: consolidated brand video pipeline.

    Uses Shotstack Create API for avatar generation (with built-in TTS lip-sync).
    No separate ElevenLabs + S3 + HeyGen calls.
    """
    create_svc = ShotstackCreateService()
    edit_svc = ShotstackService()

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

        if not brand_data["logo_url"]:
            raise ValueError("Logo not uploaded. Upload via POST /{agent_id}/logo")

        # ── 1b. AI-enhance script ─────────────────────────────
        if enhance_script:
            _update_job(job_id, status="enhancing_script")
            script_svc = ScriptGeneratorService()
            try:
                result = await script_svc.enhance_voiceover_script(
                    raw_script=script, style=style,
                    agent_name=agent_name, company_name=brand_data["company_name"],
                )
                script = result.get("enhanced_script", script)
            except Exception as e:
                logger.warning(f"Script enhancement failed, using original: {e}")
            finally:
                await script_svc.client.aclose()

        _update_job(job_id, script=script)

        # ── 2. Generate avatar with built-in TTS (single call) ─
        _update_job(job_id, status="generating_assets")

        # HeyGen text-to-avatar generates speech + lip-sync in one call
        avatar_url = await create_svc.generate_avatar(
            text=script,
            avatar=avatar_id,
            voice=avatar_voice,
            provider=avatar_provider,
            background="#FFFFFF",
            ratio="16:9",
            timeout=900,
        )
        logger.info(f"Avatar video ready: {avatar_url}")

        # Probe to get duration
        duration_info = edit_svc.probe(avatar_url)
        avatar_duration = float(duration_info.get("metadata", {}).get("duration", 120))

        # ── 3. Build Shotstack Edit timeline ──────────────────
        _update_job(job_id, status="building_timeline")

        edit = edit_svc.build_brand_video_timeline(
            logo_url=brand_data["logo_url"],
            heygen_video_url=avatar_url,
            heygen_video_duration=avatar_duration,
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

        # ── 4. Submit render ──────────────────────────────────
        _update_job(job_id, status="rendering", timeline_json=edit.to_dict())
        render_result = edit_svc.submit_render(edit)
        render_id = render_result["id"]
        _update_job(
            job_id,
            shotstack_render_id=render_id,
            duration=avatar_duration + 10,
        )
        logger.info(f"Brand video render submitted: {render_id}")

    except Exception as e:
        logger.error(f"Consolidated brand pipeline failed for job {job_id}: {e}")
        _update_job(job_id, status="failed", error=str(e)[:500])
    finally:
        create_svc.close()
        edit_svc.close()
