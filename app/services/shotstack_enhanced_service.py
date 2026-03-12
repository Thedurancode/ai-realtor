"""Shotstack Enhanced Service — Business logic extracted from the router.

Handles DB queries, data transformations, and Shotstack API interactions
for all 7 enhanced video features + media library.
"""
import logging
from typing import Dict, List, Optional, Any

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.config import settings
from app.models.agent import Agent
from app.models.agent_brand import AgentBrand
from app.models.property import Property
from app.models.property_video_job import PropertyVideoJob
from app.models.video_enhancement import (
    SocialClip, VideoBatchJob, VideoBatchItem, TemplateMarketplace,
    VideoThumbnail, ShotstackWebhook, CmaVideo, ListingSlideshow,
)
from app.services.shotstack_service import ShotstackService, STYLE_PRESETS

logger = logging.getLogger(__name__)

# ======================================================================
# Constants
# ======================================================================

ASPECT_RATIOS = {
    "16:9": {"width": 1920, "height": 1080, "resolution": "hd"},
    "9:16": {"width": 1080, "height": 1920, "resolution": "hd"},
    "1:1": {"width": 1080, "height": 1080, "resolution": "hd"},
}


# ======================================================================
# Helpers
# ======================================================================

def _hex_to_rgb(hex_color: str) -> str:
    """Convert '#RRGGBB' to 'R,G,B' for CSS rgba()."""
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return "30,58,138"  # fallback blue
    return f"{int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)}"


def _property_detail_text(prop: Property) -> str:
    parts = []
    if prop.bedrooms:
        parts.append(f"{prop.bedrooms} Bed")
    if prop.bathrooms:
        parts.append(f"{prop.bathrooms} Bath")
    if prop.square_feet:
        parts.append(f"{prop.square_feet:,} sqft")
    if prop.price:
        parts.append(f"${prop.price:,.0f}")
    return " | ".join(parts)


def _update_record(model_class, record_id: int, **kwargs):
    """Update a record in a short-lived session."""
    db = SessionLocal()
    try:
        record = db.query(model_class).filter(model_class.id == record_id).first()
        if record:
            for k, v in kwargs.items():
                setattr(record, k, v)
            db.commit()
    finally:
        db.close()


# ======================================================================
# Service class
# ======================================================================

class ShotstackEnhancedService:
    """Business logic for Shotstack enhanced video endpoints."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Shared lookups
    # ------------------------------------------------------------------

    def get_brand(self, agent_id: int) -> AgentBrand:
        brand = self.db.query(AgentBrand).filter(AgentBrand.agent_id == agent_id).first()
        if not brand:
            raise HTTPException(status_code=404, detail="Brand profile not found")
        return brand

    def get_property(self, property_id: int, agent_id: int) -> Property:
        prop = self.db.query(Property).filter(
            Property.id == property_id, Property.agent_id == agent_id
        ).first()
        if not prop:
            raise HTTPException(status_code=404, detail="Property not found")
        return prop

    # ------------------------------------------------------------------
    # Shared poll helpers
    # ------------------------------------------------------------------

    def _poll_and_update_render(self, clip: SocialClip):
        """Poll Shotstack and update social clip status."""
        try:
            shotstack = ShotstackService()
            render = shotstack.get_render_status(clip.shotstack_render_id)
            if render.get("status") == "done":
                clip.status = "done"
                clip.video_url = render.get("url")
                self.db.commit()
            elif render.get("status") == "failed":
                clip.status = "failed"
                clip.error = "Shotstack render failed"
                self.db.commit()
            shotstack.close()
        except Exception as e:
            logger.warning(f"Poll failed for social clip {clip.id}: {e}")

    def _poll_and_update_cma(self, cma: CmaVideo):
        """Poll Shotstack and update CMA video status."""
        try:
            shotstack = ShotstackService()
            render = shotstack.get_render_status(cma.shotstack_render_id)
            if render.get("status") == "done":
                cma.status = "done"
                cma.video_url = render.get("url")
                self.db.commit()
            elif render.get("status") == "failed":
                cma.status = "failed"
                cma.error = "Shotstack render failed"
                self.db.commit()
            shotstack.close()
        except Exception as e:
            logger.warning(f"Poll failed for CMA video {cma.id}: {e}")

    def _poll_and_update_slideshow(self, ss: ListingSlideshow):
        """Poll Shotstack and update slideshow status."""
        try:
            shotstack = ShotstackService()
            render = shotstack.get_render_status(ss.shotstack_render_id)
            if render.get("status") == "done":
                ss.status = "done"
                ss.video_url = render.get("url")
                self.db.commit()
            elif render.get("status") == "failed":
                ss.status = "failed"
                ss.error = "Shotstack render failed"
                self.db.commit()
            shotstack.close()
        except Exception as e:
            logger.warning(f"Poll failed for slideshow {ss.id}: {e}")

    # ------------------------------------------------------------------
    # 1. SOCIAL MEDIA CLIPS
    # ------------------------------------------------------------------

    def create_social_clip(
        self,
        agent_id: int,
        property_id: Optional[int],
        duration_target: int,
        aspect_ratio: str,
        platform: str,
        style: str,
        caption_text: Optional[str],
        hashtags: Optional[List[str]],
        background_music_url: Optional[str],
        photo_urls: Optional[List[str]],
    ) -> tuple:
        """Validate inputs, create SocialClip record, return (clip, photo_urls)."""
        if duration_target not in (15, 30, 60):
            raise HTTPException(status_code=400, detail="duration_target must be 15, 30, or 60")
        if aspect_ratio not in ASPECT_RATIOS:
            raise HTTPException(status_code=400, detail=f"aspect_ratio must be one of: {list(ASPECT_RATIOS.keys())}")

        self.get_brand(agent_id)

        resolved_photos = photo_urls or []
        if property_id:
            prop = self.get_property(property_id, agent_id)
            if not resolved_photos:
                zillow = getattr(prop, "zillow_enrichment", None)
                if zillow and zillow.photos:
                    resolved_photos = zillow.photos[:8]

        clip = SocialClip(
            agent_id=agent_id,
            property_id=property_id,
            duration_target=duration_target,
            aspect_ratio=aspect_ratio,
            resolution="hd",
            platform=platform,
            style=style,
            caption_text=caption_text,
            hashtags=hashtags,
            background_music_url=background_music_url,
            status="pending",
        )
        self.db.add(clip)
        self.db.commit()
        self.db.refresh(clip)

        return clip, resolved_photos

    def list_social_clips(self, agent_id: int, limit: int = 20) -> List[Dict]:
        clips = (
            self.db.query(SocialClip)
            .filter(SocialClip.agent_id == agent_id)
            .order_by(SocialClip.created_at.desc())
            .limit(min(limit, 100))
            .all()
        )
        return [
            {
                "clip_id": c.id,
                "property_id": c.property_id,
                "duration_target": c.duration_target,
                "aspect_ratio": c.aspect_ratio,
                "platform": c.platform,
                "status": c.status,
                "video_url": c.video_url,
                "thumbnail_url": c.thumbnail_url,
                "created_at": c.created_at,
            }
            for c in clips
        ]

    def get_social_clip(self, clip_id: int) -> Dict:
        clip = self.db.query(SocialClip).filter(SocialClip.id == clip_id).first()
        if not clip:
            raise HTTPException(status_code=404, detail="Social clip not found")

        if clip.status == "rendering" and clip.shotstack_render_id:
            self._poll_and_update_render(clip)

        return {
            "clip_id": clip.id,
            "agent_id": clip.agent_id,
            "property_id": clip.property_id,
            "duration_target": clip.duration_target,
            "actual_duration": clip.actual_duration,
            "aspect_ratio": clip.aspect_ratio,
            "platform": clip.platform,
            "style": clip.style,
            "status": clip.status,
            "video_url": clip.video_url,
            "thumbnail_url": clip.thumbnail_url,
            "caption_text": clip.caption_text,
            "hashtags": clip.hashtags,
            "error": clip.error,
            "timeline_json": clip.timeline_json,
            "created_at": clip.created_at,
        }

    # ------------------------------------------------------------------
    # 2. BATCH RENDERING
    # ------------------------------------------------------------------

    def create_batch_render(
        self,
        agent_id: int,
        property_ids: List[int],
        job_type: str,
        style: str,
        name: Optional[str],
    ) -> Dict:
        """Validate properties, create batch job + items, return batch info."""
        properties = (
            self.db.query(Property)
            .filter(Property.id.in_(property_ids), Property.agent_id == agent_id)
            .all()
        )
        found_ids = {p.id for p in properties}
        missing = set(property_ids) - found_ids
        if missing:
            raise HTTPException(status_code=404, detail=f"Properties not found: {sorted(missing)}")

        batch = VideoBatchJob(
            agent_id=agent_id,
            name=name or f"Batch {job_type} ({len(property_ids)} properties)",
            job_type=job_type,
            style=style,
            status="pending",
            total_items=len(property_ids),
        )
        self.db.add(batch)
        self.db.commit()
        self.db.refresh(batch)

        for pid in property_ids:
            item = VideoBatchItem(
                batch_id=batch.id,
                property_id=pid,
                status="pending",
            )
            self.db.add(item)
        self.db.commit()

        return {
            "batch_id": batch.id,
            "status": "pending",
            "total_items": len(property_ids),
            "message": f"Batch rendering started for {len(property_ids)} properties.",
        }

    def list_batch_jobs(self, agent_id: int, limit: int = 20) -> List[Dict]:
        batches = (
            self.db.query(VideoBatchJob)
            .filter(VideoBatchJob.agent_id == agent_id)
            .order_by(VideoBatchJob.created_at.desc())
            .limit(min(limit, 100))
            .all()
        )
        return [
            {
                "batch_id": b.id,
                "name": b.name,
                "job_type": b.job_type,
                "style": b.style,
                "status": b.status,
                "total_items": b.total_items,
                "completed_items": b.completed_items,
                "failed_items": b.failed_items,
                "created_at": b.created_at,
            }
            for b in batches
        ]

    def get_batch_job(self, batch_id: int) -> Dict:
        batch = self.db.query(VideoBatchJob).filter(VideoBatchJob.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch job not found")

        items = (
            self.db.query(VideoBatchItem)
            .filter(VideoBatchItem.batch_id == batch_id)
            .all()
        )

        return {
            "batch_id": batch.id,
            "name": batch.name,
            "job_type": batch.job_type,
            "style": batch.style,
            "status": batch.status,
            "total_items": batch.total_items,
            "completed_items": batch.completed_items,
            "failed_items": batch.failed_items,
            "created_at": batch.created_at,
            "items": [
                {
                    "item_id": item.id,
                    "property_id": item.property_id,
                    "video_job_id": item.video_job_id,
                    "status": item.status,
                    "video_url": item.video_url,
                    "error": item.error,
                }
                for item in items
            ],
        }

    # ------------------------------------------------------------------
    # 3. TEMPLATE MARKETPLACE
    # ------------------------------------------------------------------

    def list_marketplace_templates(
        self,
        category: Optional[str] = None,
        style: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        featured_only: bool = False,
        limit: int = 20,
    ) -> List[Dict]:
        query = self.db.query(TemplateMarketplace)
        if category:
            query = query.filter(TemplateMarketplace.category == category)
        if style:
            query = query.filter(TemplateMarketplace.style == style)
        if aspect_ratio:
            query = query.filter(TemplateMarketplace.aspect_ratio == aspect_ratio)
        if featured_only:
            query = query.filter(TemplateMarketplace.is_featured == True)

        templates = query.order_by(TemplateMarketplace.use_count.desc()).limit(min(limit, 100)).all()

        return [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "style": t.style,
                "aspect_ratio": t.aspect_ratio,
                "duration": t.duration,
                "preview_image_url": t.preview_image_url,
                "preview_video_url": t.preview_video_url,
                "merge_fields": t.merge_fields,
                "tags": t.tags,
                "is_featured": t.is_featured,
                "is_premium": t.is_premium,
                "use_count": t.use_count,
            }
            for t in templates
        ]

    def get_marketplace_template(self, template_id: int) -> Dict:
        t = self.db.query(TemplateMarketplace).filter(TemplateMarketplace.id == template_id).first()
        if not t:
            raise HTTPException(status_code=404, detail="Template not found")
        return {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "category": t.category,
            "style": t.style,
            "aspect_ratio": t.aspect_ratio,
            "duration": t.duration,
            "preview_image_url": t.preview_image_url,
            "preview_video_url": t.preview_video_url,
            "template_json": t.template_json,
            "merge_fields": t.merge_fields,
            "tags": t.tags,
            "is_featured": t.is_featured,
            "is_premium": t.is_premium,
            "use_count": t.use_count,
            "shotstack_template_id": t.shotstack_template_id,
            "created_at": t.created_at,
        }

    def create_marketplace_template(
        self,
        name: str,
        description: Optional[str],
        category: str,
        style: str,
        template_json: Dict[str, Any],
        merge_fields: Optional[List[Dict[str, str]]],
        aspect_ratio: str,
        duration: Optional[float],
        tags: Optional[List[str]],
        preview_image_url: Optional[str],
        preview_video_url: Optional[str],
        is_premium: bool,
        agent_id: Optional[int] = None,
    ) -> Dict:
        template = TemplateMarketplace(
            name=name,
            description=description,
            category=category,
            style=style,
            template_json=template_json,
            merge_fields=merge_fields,
            aspect_ratio=aspect_ratio,
            duration=duration,
            tags=tags,
            preview_image_url=preview_image_url,
            preview_video_url=preview_video_url,
            is_premium=is_premium,
            created_by_agent_id=agent_id,
        )

        # Optionally save to Shotstack as well
        if settings.shotstack_api_key:
            try:
                shotstack = ShotstackService()
                api_client = shotstack._api_client
                edit_obj = api_client._ApiClient__deserialize(template_json, 'Edit')
                ss_id = shotstack.save_template(name, edit_obj)
                template.shotstack_template_id = ss_id
                shotstack.close()
            except Exception as e:
                logger.warning(f"Failed to save to Shotstack: {e}")

        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)

        return {
            "id": template.id,
            "name": template.name,
            "shotstack_template_id": template.shotstack_template_id,
            "message": "Template added to marketplace.",
        }

    def render_marketplace_template(
        self,
        template_id: int,
        merge_fields: Optional[Dict[str, str]] = None,
    ) -> Dict:
        template = self.db.query(TemplateMarketplace).filter(TemplateMarketplace.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        shotstack = ShotstackService()
        try:
            if template.shotstack_template_id:
                result = shotstack.render_template(template.shotstack_template_id, merge_fields)
            else:
                api_client = shotstack._api_client
                edit_obj = api_client._ApiClient__deserialize(template.template_json, 'Edit')
                result = shotstack.submit_render(edit_obj)

            template.use_count = (template.use_count or 0) + 1
            self.db.commit()

            return {
                "render_id": result["id"],
                "status": result.get("status", "queued"),
                "template_id": template_id,
                "message": "Render submitted.",
            }
        finally:
            shotstack.close()

    def delete_marketplace_template(self, template_id: int) -> Dict:
        template = self.db.query(TemplateMarketplace).filter(TemplateMarketplace.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        if template.shotstack_template_id and settings.shotstack_api_key:
            try:
                shotstack = ShotstackService()
                shotstack.delete_template(template.shotstack_template_id)
                shotstack.close()
            except Exception as e:
                logger.warning(f"Failed to delete Shotstack template: {e}")

        self.db.delete(template)
        self.db.commit()
        return {"message": "Template deleted.", "id": template_id}

    # ------------------------------------------------------------------
    # 4. VIDEO PREVIEW / THUMBNAIL
    # ------------------------------------------------------------------

    def create_thumbnail(
        self,
        agent_id: int,
        source_type: str,
        source_id: int,
        frame_time: float,
    ) -> tuple:
        """Validate source, create thumbnail record. Returns (thumb, timeline_json)."""
        source_map = {
            "property_video_job": PropertyVideoJob,
            "social_clip": SocialClip,
            "cma_video": CmaVideo,
            "slideshow": ListingSlideshow,
        }
        model_class = source_map.get(source_type)
        if not model_class:
            raise HTTPException(status_code=400, detail=f"Invalid source_type. Must be one of: {list(source_map.keys())}")

        source = self.db.query(model_class).filter(model_class.id == source_id).first()
        if not source:
            raise HTTPException(status_code=404, detail=f"{source_type} #{source_id} not found")

        timeline_json = getattr(source, "timeline_json", None)
        if not timeline_json:
            raise HTTPException(status_code=400, detail="No timeline stored for this job. Wait for timeline to be built.")

        thumb = VideoThumbnail(
            agent_id=agent_id,
            source_type=source_type,
            source_id=source_id,
            frame_time=frame_time,
            status="pending",
        )
        self.db.add(thumb)
        self.db.commit()
        self.db.refresh(thumb)

        return thumb, timeline_json

    def get_thumbnail(self, thumbnail_id: int) -> Dict:
        thumb = self.db.query(VideoThumbnail).filter(VideoThumbnail.id == thumbnail_id).first()
        if not thumb:
            raise HTTPException(status_code=404, detail="Thumbnail not found")

        if thumb.status == "rendering" and thumb.shotstack_render_id:
            try:
                shotstack = ShotstackService()
                render = shotstack.get_render_status(thumb.shotstack_render_id)
                if render.get("status") == "done":
                    thumb.status = "done"
                    thumb.thumbnail_url = render.get("url")
                    self.db.commit()
                elif render.get("status") == "failed":
                    thumb.status = "failed"
                    self.db.commit()
                shotstack.close()
            except Exception:
                pass

        return {
            "thumbnail_id": thumb.id,
            "source_type": thumb.source_type,
            "source_id": thumb.source_id,
            "status": thumb.status,
            "thumbnail_url": thumb.thumbnail_url,
            "frame_time": thumb.frame_time,
            "created_at": thumb.created_at,
        }

    # ------------------------------------------------------------------
    # 5. WEBHOOK CALLBACK
    # ------------------------------------------------------------------

    def handle_webhook_callback(self, payload: Dict) -> Dict:
        data = payload.get("data", {})
        render_id = data.get("id")
        status = data.get("status", "unknown")
        video_url = data.get("url")
        action = payload.get("action", "")

        if not render_id:
            raise HTTPException(status_code=400, detail="Missing render ID in payload")

        webhook_log = ShotstackWebhook(
            render_id=render_id,
            status=status,
            video_url=video_url,
            payload=payload,
        )

        updated = False

        # Check PropertyVideoJob
        job = self.db.query(PropertyVideoJob).filter(PropertyVideoJob.shotstack_render_id == render_id).first()
        if job:
            webhook_log.job_type = "property_video"
            webhook_log.job_id = job.id
            if status == "done":
                job.status = "done"
                job.video_url = video_url
            elif status == "failed":
                job.status = "failed"
                job.error = "Shotstack render failed (webhook)"
            updated = True

        # Check SocialClip
        if not updated:
            clip = self.db.query(SocialClip).filter(SocialClip.shotstack_render_id == render_id).first()
            if clip:
                webhook_log.job_type = "social_clip"
                webhook_log.job_id = clip.id
                if status == "done":
                    clip.status = "done"
                    clip.video_url = video_url
                elif status == "failed":
                    clip.status = "failed"
                    clip.error = "Shotstack render failed (webhook)"
                updated = True

        # Check CmaVideo
        if not updated:
            cma = self.db.query(CmaVideo).filter(CmaVideo.shotstack_render_id == render_id).first()
            if cma:
                webhook_log.job_type = "cma_video"
                webhook_log.job_id = cma.id
                if status == "done":
                    cma.status = "done"
                    cma.video_url = video_url
                elif status == "failed":
                    cma.status = "failed"
                    cma.error = "Shotstack render failed (webhook)"
                updated = True

        # Check ListingSlideshow
        if not updated:
            ss = self.db.query(ListingSlideshow).filter(ListingSlideshow.shotstack_render_id == render_id).first()
            if ss:
                webhook_log.job_type = "slideshow"
                webhook_log.job_id = ss.id
                if status == "done":
                    ss.status = "done"
                    ss.video_url = video_url
                elif status == "failed":
                    ss.status = "failed"
                    ss.error = "Shotstack render failed (webhook)"
                updated = True

        # Check VideoThumbnail
        if not updated:
            thumb = self.db.query(VideoThumbnail).filter(VideoThumbnail.shotstack_render_id == render_id).first()
            if thumb:
                webhook_log.job_type = "thumbnail"
                webhook_log.job_id = thumb.id
                if status == "done":
                    thumb.status = "done"
                    thumb.thumbnail_url = video_url
                elif status == "failed":
                    thumb.status = "failed"
                updated = True

        self.db.add(webhook_log)
        self.db.commit()

        logger.info(f"Shotstack webhook: render={render_id} status={status} updated={updated}")
        return {"received": True, "render_id": render_id, "updated": updated}

    def list_webhook_logs(self, limit: int = 20) -> List[Dict]:
        logs = (
            self.db.query(ShotstackWebhook)
            .order_by(ShotstackWebhook.received_at.desc())
            .limit(min(limit, 100))
            .all()
        )
        return [
            {
                "id": l.id,
                "render_id": l.render_id,
                "job_type": l.job_type,
                "job_id": l.job_id,
                "status": l.status,
                "video_url": l.video_url,
                "received_at": l.received_at,
            }
            for l in logs
        ]

    # ------------------------------------------------------------------
    # 6. CMA / MARKET REPORT VIDEOS
    # ------------------------------------------------------------------

    def create_cma_video(
        self,
        agent_id: int,
        property_id: int,
        style: str,
        max_comps: int,
        include_rentals: bool,
    ) -> tuple:
        """Validate, create CmaVideo record. Returns (cma, prop)."""
        self.get_brand(agent_id)
        prop = self.get_property(property_id, agent_id)

        cma = CmaVideo(
            agent_id=agent_id,
            property_id=property_id,
            style=style,
            max_comps=max_comps,
            include_rentals=include_rentals,
            status="pending",
        )
        self.db.add(cma)
        self.db.commit()
        self.db.refresh(cma)

        return cma, prop

    def list_cma_videos(self, agent_id: int, limit: int = 20) -> List[Dict]:
        vids = (
            self.db.query(CmaVideo)
            .filter(CmaVideo.agent_id == agent_id)
            .order_by(CmaVideo.created_at.desc())
            .limit(min(limit, 100))
            .all()
        )
        return [
            {
                "cma_video_id": v.id,
                "property_id": v.property_id,
                "style": v.style,
                "max_comps": v.max_comps,
                "status": v.status,
                "video_url": v.video_url,
                "created_at": v.created_at,
            }
            for v in vids
        ]

    def get_cma_video(self, cma_id: int) -> Dict:
        cma = self.db.query(CmaVideo).filter(CmaVideo.id == cma_id).first()
        if not cma:
            raise HTTPException(status_code=404, detail="CMA video not found")

        if cma.status == "rendering" and cma.shotstack_render_id:
            self._poll_and_update_cma(cma)

        return {
            "cma_video_id": cma.id,
            "agent_id": cma.agent_id,
            "property_id": cma.property_id,
            "style": cma.style,
            "max_comps": cma.max_comps,
            "include_rentals": cma.include_rentals,
            "status": cma.status,
            "video_url": cma.video_url,
            "thumbnail_url": cma.thumbnail_url,
            "duration": cma.duration,
            "comp_data": cma.comp_data,
            "script": cma.script,
            "error": cma.error,
            "created_at": cma.created_at,
        }

    # ------------------------------------------------------------------
    # 7. LISTING SLIDESHOW
    # ------------------------------------------------------------------

    def create_listing_slideshow(
        self,
        agent_id: int,
        property_id: int,
        style: str,
        photo_urls: Optional[List[str]],
        title_text: Optional[str],
        subtitle_text: Optional[str],
        cta_text: Optional[str],
        background_music_url: Optional[str],
        aspect_ratio: str,
        seconds_per_photo: float,
    ) -> tuple:
        """Validate, create ListingSlideshow record. Returns (slideshow, photo_urls)."""
        self.get_brand(agent_id)
        prop = self.get_property(property_id, agent_id)

        resolved_photos = photo_urls
        if not resolved_photos:
            zillow = getattr(prop, "zillow_enrichment", None)
            if zillow and zillow.photos:
                resolved_photos = zillow.photos[:10]
        if not resolved_photos:
            raise HTTPException(status_code=400, detail="No photos available. Provide photo_urls or enrich the property first.")

        slideshow = ListingSlideshow(
            agent_id=agent_id,
            property_id=property_id,
            style=style,
            photo_urls=resolved_photos,
            title_text=title_text or prop.address,
            subtitle_text=subtitle_text or _property_detail_text(prop),
            cta_text=cta_text,
            background_music_url=background_music_url,
            aspect_ratio=aspect_ratio,
            seconds_per_photo=seconds_per_photo,
            status="pending",
        )
        self.db.add(slideshow)
        self.db.commit()
        self.db.refresh(slideshow)

        return slideshow, resolved_photos

    def list_slideshows(self, agent_id: int, limit: int = 20) -> List[Dict]:
        shows = (
            self.db.query(ListingSlideshow)
            .filter(ListingSlideshow.agent_id == agent_id)
            .order_by(ListingSlideshow.created_at.desc())
            .limit(min(limit, 100))
            .all()
        )
        return [
            {
                "slideshow_id": s.id,
                "property_id": s.property_id,
                "style": s.style,
                "status": s.status,
                "video_url": s.video_url,
                "duration": s.duration,
                "aspect_ratio": s.aspect_ratio,
                "created_at": s.created_at,
            }
            for s in shows
        ]

    def get_slideshow(self, slideshow_id: int) -> Dict:
        ss = self.db.query(ListingSlideshow).filter(ListingSlideshow.id == slideshow_id).first()
        if not ss:
            raise HTTPException(status_code=404, detail="Slideshow not found")

        if ss.status == "rendering" and ss.shotstack_render_id:
            self._poll_and_update_slideshow(ss)

        return {
            "slideshow_id": ss.id,
            "agent_id": ss.agent_id,
            "property_id": ss.property_id,
            "style": ss.style,
            "status": ss.status,
            "video_url": ss.video_url,
            "thumbnail_url": ss.thumbnail_url,
            "duration": ss.duration,
            "photo_urls": ss.photo_urls,
            "title_text": ss.title_text,
            "subtitle_text": ss.subtitle_text,
            "cta_text": ss.cta_text,
            "aspect_ratio": ss.aspect_ratio,
            "seconds_per_photo": ss.seconds_per_photo,
            "error": ss.error,
            "timeline_json": ss.timeline_json,
            "created_at": ss.created_at,
        }

    # ------------------------------------------------------------------
    # 8. MEDIA LIBRARY
    # ------------------------------------------------------------------

    def get_property_rendered_media(
        self,
        property_id: int,
        agent_id: int,
        status_filter: Optional[str] = None,
        media_type: Optional[str] = None,
        limit: int = 50,
    ) -> Dict:
        results = []

        # Property Videos
        if not media_type or media_type == "property_video":
            q = self.db.query(PropertyVideoJob).filter(
                PropertyVideoJob.property_id == property_id,
                PropertyVideoJob.agent_id == agent_id,
            )
            if status_filter:
                q = q.filter(PropertyVideoJob.status == status_filter)
            for v in q.order_by(PropertyVideoJob.created_at.desc()).limit(limit).all():
                results.append({
                    "id": v.id,
                    "media_type": "property_video",
                    "status": v.status,
                    "video_url": v.video_url,
                    "thumbnail_url": None,
                    "style": v.style,
                    "duration": v.duration,
                    "pipeline_type": v.pipeline_type,
                    "render_id": v.shotstack_render_id,
                    "has_timeline": v.timeline_json is not None,
                    "created_at": v.created_at,
                })

        # Social Clips
        if not media_type or media_type == "social_clip":
            q = self.db.query(SocialClip).filter(
                SocialClip.property_id == property_id,
                SocialClip.agent_id == agent_id,
            )
            if status_filter:
                q = q.filter(SocialClip.status == status_filter)
            for c in q.order_by(SocialClip.created_at.desc()).limit(limit).all():
                results.append({
                    "id": c.id,
                    "media_type": "social_clip",
                    "status": c.status,
                    "video_url": c.video_url,
                    "thumbnail_url": c.thumbnail_url,
                    "style": c.style,
                    "duration": c.actual_duration,
                    "aspect_ratio": c.aspect_ratio,
                    "platform": c.platform,
                    "duration_target": c.duration_target,
                    "render_id": c.shotstack_render_id,
                    "has_timeline": c.timeline_json is not None,
                    "created_at": c.created_at,
                })

        # CMA Videos
        if not media_type or media_type == "cma_video":
            q = self.db.query(CmaVideo).filter(
                CmaVideo.property_id == property_id,
                CmaVideo.agent_id == agent_id,
            )
            if status_filter:
                q = q.filter(CmaVideo.status == status_filter)
            for v in q.order_by(CmaVideo.created_at.desc()).limit(limit).all():
                results.append({
                    "id": v.id,
                    "media_type": "cma_video",
                    "status": v.status,
                    "video_url": v.video_url,
                    "thumbnail_url": v.thumbnail_url,
                    "style": v.style,
                    "duration": v.duration,
                    "max_comps": v.max_comps,
                    "render_id": v.shotstack_render_id,
                    "has_timeline": v.timeline_json is not None,
                    "created_at": v.created_at,
                })

        # Listing Slideshows
        if not media_type or media_type == "slideshow":
            q = self.db.query(ListingSlideshow).filter(
                ListingSlideshow.property_id == property_id,
                ListingSlideshow.agent_id == agent_id,
            )
            if status_filter:
                q = q.filter(ListingSlideshow.status == status_filter)
            for s in q.order_by(ListingSlideshow.created_at.desc()).limit(limit).all():
                results.append({
                    "id": s.id,
                    "media_type": "slideshow",
                    "status": s.status,
                    "video_url": s.video_url,
                    "thumbnail_url": s.thumbnail_url,
                    "style": s.style,
                    "duration": s.duration,
                    "aspect_ratio": s.aspect_ratio,
                    "photo_count": len(s.photo_urls) if s.photo_urls else 0,
                    "render_id": s.shotstack_render_id,
                    "has_timeline": s.timeline_json is not None,
                    "created_at": s.created_at,
                })

        # Thumbnails
        if not media_type or media_type == "thumbnail":
            video_ids = [r["id"] for r in results if r["media_type"] == "property_video"]
            clip_ids = [r["id"] for r in results if r["media_type"] == "social_clip"]
            slideshow_ids = [r["id"] for r in results if r["media_type"] == "slideshow"]
            cma_ids = [r["id"] for r in results if r["media_type"] == "cma_video"]

            thumb_q = self.db.query(VideoThumbnail).filter(
                VideoThumbnail.agent_id == agent_id,
            )
            if status_filter:
                thumb_q = thumb_q.filter(VideoThumbnail.status == status_filter)

            for t in thumb_q.order_by(VideoThumbnail.created_at.desc()).limit(limit).all():
                match = (
                    (t.source_type == "property_video_job" and t.source_id in video_ids)
                    or (t.source_type == "social_clip" and t.source_id in clip_ids)
                    or (t.source_type == "slideshow" and t.source_id in slideshow_ids)
                    or (t.source_type == "cma_video" and t.source_id in cma_ids)
                )
                if match:
                    results.append({
                        "id": t.id,
                        "media_type": "thumbnail",
                        "status": t.status,
                        "video_url": None,
                        "thumbnail_url": t.thumbnail_url,
                        "source_type": t.source_type,
                        "source_id": t.source_id,
                        "frame_time": t.frame_time,
                        "render_id": t.shotstack_render_id,
                        "has_timeline": False,
                        "created_at": t.created_at,
                    })

        results.sort(key=lambda r: r["created_at"] or "", reverse=True)

        done_count = sum(1 for r in results if r["status"] == "done")
        total_count = len(results)

        return {
            "property_id": property_id,
            "agent_id": agent_id,
            "total": total_count,
            "done": done_count,
            "rendering": sum(1 for r in results if r["status"] == "rendering"),
            "failed": sum(1 for r in results if r["status"] == "failed"),
            "media": results[:limit],
            "by_type": {
                "property_video": sum(1 for r in results if r["media_type"] == "property_video"),
                "social_clip": sum(1 for r in results if r["media_type"] == "social_clip"),
                "cma_video": sum(1 for r in results if r["media_type"] == "cma_video"),
                "slideshow": sum(1 for r in results if r["media_type"] == "slideshow"),
                "thumbnail": sum(1 for r in results if r["media_type"] == "thumbnail"),
            },
        }

    def get_agent_rendered_media(
        self,
        agent_id: int,
        status_filter: Optional[str] = None,
        media_type: Optional[str] = None,
        limit: int = 50,
    ) -> Dict:
        results = []

        if not media_type or media_type == "property_video":
            q = self.db.query(PropertyVideoJob).filter(PropertyVideoJob.agent_id == agent_id)
            if status_filter:
                q = q.filter(PropertyVideoJob.status == status_filter)
            for v in q.order_by(PropertyVideoJob.created_at.desc()).limit(limit).all():
                results.append({
                    "id": v.id,
                    "media_type": "property_video",
                    "property_id": v.property_id,
                    "status": v.status,
                    "video_url": v.video_url,
                    "thumbnail_url": None,
                    "style": v.style,
                    "duration": v.duration,
                    "pipeline_type": v.pipeline_type,
                    "render_id": v.shotstack_render_id,
                    "has_timeline": v.timeline_json is not None,
                    "created_at": v.created_at,
                })

        if not media_type or media_type == "social_clip":
            q = self.db.query(SocialClip).filter(SocialClip.agent_id == agent_id)
            if status_filter:
                q = q.filter(SocialClip.status == status_filter)
            for c in q.order_by(SocialClip.created_at.desc()).limit(limit).all():
                results.append({
                    "id": c.id,
                    "media_type": "social_clip",
                    "property_id": c.property_id,
                    "status": c.status,
                    "video_url": c.video_url,
                    "thumbnail_url": c.thumbnail_url,
                    "style": c.style,
                    "duration": c.actual_duration,
                    "aspect_ratio": c.aspect_ratio,
                    "platform": c.platform,
                    "render_id": c.shotstack_render_id,
                    "has_timeline": c.timeline_json is not None,
                    "created_at": c.created_at,
                })

        if not media_type or media_type == "cma_video":
            q = self.db.query(CmaVideo).filter(CmaVideo.agent_id == agent_id)
            if status_filter:
                q = q.filter(CmaVideo.status == status_filter)
            for v in q.order_by(CmaVideo.created_at.desc()).limit(limit).all():
                results.append({
                    "id": v.id,
                    "media_type": "cma_video",
                    "property_id": v.property_id,
                    "status": v.status,
                    "video_url": v.video_url,
                    "thumbnail_url": v.thumbnail_url,
                    "style": v.style,
                    "duration": v.duration,
                    "render_id": v.shotstack_render_id,
                    "has_timeline": v.timeline_json is not None,
                    "created_at": v.created_at,
                })

        if not media_type or media_type == "slideshow":
            q = self.db.query(ListingSlideshow).filter(ListingSlideshow.agent_id == agent_id)
            if status_filter:
                q = q.filter(ListingSlideshow.status == status_filter)
            for s in q.order_by(ListingSlideshow.created_at.desc()).limit(limit).all():
                results.append({
                    "id": s.id,
                    "media_type": "slideshow",
                    "property_id": s.property_id,
                    "status": s.status,
                    "video_url": s.video_url,
                    "thumbnail_url": s.thumbnail_url,
                    "style": s.style,
                    "duration": s.duration,
                    "aspect_ratio": s.aspect_ratio,
                    "photo_count": len(s.photo_urls) if s.photo_urls else 0,
                    "render_id": s.shotstack_render_id,
                    "has_timeline": s.timeline_json is not None,
                    "created_at": s.created_at,
                })

        results.sort(key=lambda r: r["created_at"] or "", reverse=True)
        results = results[:limit]

        done_count = sum(1 for r in results if r["status"] == "done")

        return {
            "agent_id": agent_id,
            "total": len(results),
            "done": done_count,
            "rendering": sum(1 for r in results if r["status"] == "rendering"),
            "failed": sum(1 for r in results if r["status"] == "failed"),
            "media": results,
            "by_type": {
                "property_video": sum(1 for r in results if r["media_type"] == "property_video"),
                "social_clip": sum(1 for r in results if r["media_type"] == "social_clip"),
                "cma_video": sum(1 for r in results if r["media_type"] == "cma_video"),
                "slideshow": sum(1 for r in results if r["media_type"] == "slideshow"),
            },
        }

    def get_media_timeline(self, media_type: str, media_id: int) -> Dict:
        model_map = {
            "property_video": PropertyVideoJob,
            "social_clip": SocialClip,
            "cma_video": CmaVideo,
            "slideshow": ListingSlideshow,
        }

        model = model_map.get(media_type)
        if not model:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid media_type. Must be one of: {list(model_map.keys())}"
            )

        record = self.db.query(model).filter(model.id == media_id).first()
        if not record:
            raise HTTPException(status_code=404, detail=f"{media_type} not found")

        timeline = getattr(record, "timeline_json", None)
        if not timeline:
            raise HTTPException(
                status_code=404,
                detail=f"No timeline data saved for this {media_type}. It may have been rendered externally."
            )

        return {
            "id": media_id,
            "media_type": media_type,
            "status": record.status,
            "video_url": record.video_url,
            "render_id": record.shotstack_render_id,
            "timeline_json": timeline,
            "created_at": record.created_at,
        }


# ======================================================================
# Background task functions (module-level, use their own DB sessions)
# ======================================================================

async def render_social_clip_task(
    clip_id: int,
    agent_id: int,
    photo_urls: List[str],
    custom_texts: Optional[List[str]],
    property_id: Optional[int],
):
    """Background task: build and submit a social clip to Shotstack."""
    shotstack = ShotstackService()
    try:
        _update_record(SocialClip, clip_id, status="building_timeline")

        db = SessionLocal()
        try:
            clip = db.query(SocialClip).filter(SocialClip.id == clip_id).first()
            brand = db.query(AgentBrand).filter(AgentBrand.agent_id == agent_id).first()
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            prop = None
            if property_id:
                prop = db.query(Property).filter(Property.id == property_id).first()

            if not clip or not brand or not agent:
                raise ValueError("Missing clip, brand, or agent data")

            primary_color = brand.primary_color or "#1E3A8A"
            text_color = brand.text_color or "#FFFFFF"
            agent_name = agent.name
            logo_url = brand.logo_url
            preset = STYLE_PRESETS.get(clip.style, STYLE_PRESETS["professional"])
            ar = ASPECT_RATIOS.get(clip.aspect_ratio, ASPECT_RATIOS["9:16"])

            address = prop.address if prop else ""
            details = _property_detail_text(prop) if prop else ""
            display_phone = brand.display_phone or ""
            display_email = brand.display_email or ""
            bg_music_url = clip.background_music_url
            clip_style = clip.style
            clip_duration = clip.duration_target
            clip_aspect = clip.aspect_ratio
        finally:
            db.close()

        duration = clip_duration
        num_photos = min(len(photo_urls), max(1, duration // 4))
        scene_len = duration / max(num_photos, 1)

        clips_spec = []
        offset = 0.0

        for i in range(num_photos):
            clips_spec.append({
                "type": "image",
                "src": photo_urls[i],
                "start": offset,
                "length": scene_len,
                "track": 1,
                "fit": "cover",
                "effect": "zoomInSlow" if i % 2 == 0 else "zoomOutSlow",
                "transition_in": "fade",
                "transition_out": "fade",
            })

            text = ""
            if custom_texts and i < len(custom_texts):
                text = custom_texts[i]
            elif i == 0 and address:
                text = address
            elif i == 1 and details:
                text = details

            if text:
                font_size = 28 if ar["width"] < ar["height"] else 32
                css = (
                    f"font-family:{preset['body_font']};"
                    f"font-size:{font_size}px;"
                    f"color:{text_color};"
                    f"background:rgba({_hex_to_rgb(primary_color)},0.75);"
                    f"padding:10px 20px;"
                    f"border-radius:8px;"
                    f"text-align:center;"
                )
                clips_spec.append({
                    "type": "html",
                    "html": f'<div style="{css}">{text}</div>',
                    "start": offset,
                    "length": scene_len,
                    "track": 0,
                    "position": "bottom",
                    "offset_y": -0.08,
                    "width": int(ar["width"] * 0.85),
                    "height": 100,
                })

            offset += scene_len

        if logo_url:
            clips_spec.append({
                "type": "image",
                "src": logo_url,
                "start": 0,
                "length": duration,
                "track": 0,
                "position": "topRight",
                "scale": 0.1,
                "offset_x": -0.03,
                "offset_y": -0.03,
                "opacity": 0.8,
                "fit": "none",
            })

        contact_parts = [p for p in [agent_name, display_phone, display_email] if p]
        if contact_parts:
            cta_css = (
                f"font-family:Arial,sans-serif;font-size:24px;color:{text_color};"
                f"background:rgba({_hex_to_rgb(primary_color)},0.85);"
                f"padding:12px 24px;border-radius:8px;text-align:center;"
            )
            last_scene_start = max(0, offset - scene_len)
            clips_spec.append({
                "type": "html",
                "html": f'<div style="{cta_css}">{"<br>".join(contact_parts)}</div>',
                "start": last_scene_start,
                "length": scene_len,
                "track": 0,
                "position": "bottom",
                "offset_y": -0.15,
                "width": int(ar["width"] * 0.85),
                "height": 120,
                "transition_in": "fade",
            })

        edit = shotstack.build_custom_timeline(
            clips_spec,
            background=primary_color,
            soundtrack_url=bg_music_url,
            soundtrack_volume=0.20,
        )

        from shotstack_sdk.model.output import Output
        from shotstack_sdk.model.size import Size
        edit.output = Output(
            format="mp4",
            resolution=ar["resolution"],
            fps=30.0,
            size=Size(width=ar["width"], height=ar["height"]),
        )

        _update_record(SocialClip, clip_id, status="rendering", timeline_json=edit.to_dict())
        render_result = shotstack.submit_render(edit)
        render_id = render_result["id"]
        _update_record(
            SocialClip, clip_id,
            shotstack_render_id=render_id,
            actual_duration=offset,
        )
        logger.info(f"Social clip {clip_id} submitted to Shotstack: {render_id}")

    except Exception as e:
        logger.error(f"Social clip {clip_id} failed: {e}")
        _update_record(SocialClip, clip_id, status="failed", error=str(e)[:500])
    finally:
        shotstack.close()


async def process_batch_task(batch_id: int, agent_id: int, job_type: str, style: str):
    """Background: process each item in a batch sequentially."""
    _update_record(VideoBatchJob, batch_id, status="processing")

    db = SessionLocal()
    try:
        items = db.query(VideoBatchItem).filter(VideoBatchItem.batch_id == batch_id).all()
        completed = 0
        failed = 0

        for item in items:
            try:
                _update_record(VideoBatchItem, item.id, status="processing")

                if job_type == "slideshow":
                    prop = db.query(Property).filter(Property.id == item.property_id).first()
                    zillow = getattr(prop, "zillow_enrichment", None) if prop else None
                    photo_urls = (zillow.photos or [])[:10] if zillow else []

                    if not photo_urls:
                        raise ValueError("No photos available for slideshow")

                    slideshow = ListingSlideshow(
                        agent_id=agent_id,
                        property_id=item.property_id,
                        style=style,
                        photo_urls=photo_urls,
                        title_text=prop.address if prop else "",
                        subtitle_text=_property_detail_text(prop) if prop else "",
                        status="pending",
                    )
                    db.add(slideshow)
                    db.commit()
                    db.refresh(slideshow)

                    await render_listing_slideshow_task(slideshow.id, agent_id)
                    db.refresh(slideshow)
                    _update_record(
                        VideoBatchItem, item.id,
                        status="done" if slideshow.status == "done" else slideshow.status,
                        video_url=slideshow.video_url,
                        video_job_id=slideshow.id,
                    )

                elif job_type == "social_clip":
                    prop = db.query(Property).filter(Property.id == item.property_id).first()
                    zillow = getattr(prop, "zillow_enrichment", None) if prop else None
                    photo_urls = (zillow.photos or [])[:6] if zillow else []

                    clip = SocialClip(
                        agent_id=agent_id,
                        property_id=item.property_id,
                        duration_target=30,
                        aspect_ratio="9:16",
                        platform="all",
                        style=style,
                        status="pending",
                    )
                    db.add(clip)
                    db.commit()
                    db.refresh(clip)

                    await render_social_clip_task(clip.id, agent_id, photo_urls, None, item.property_id)
                    db.refresh(clip)
                    _update_record(
                        VideoBatchItem, item.id,
                        status="rendering",
                        video_job_id=clip.id,
                    )

                else:
                    job = PropertyVideoJob(
                        agent_id=agent_id,
                        property_id=item.property_id,
                        style=style,
                        status="pending",
                    )
                    db.add(job)
                    db.commit()
                    db.refresh(job)
                    _update_record(
                        VideoBatchItem, item.id,
                        status="queued",
                        video_job_id=job.id,
                    )

                completed += 1

            except Exception as e:
                logger.error(f"Batch item {item.id} failed: {e}")
                _update_record(
                    VideoBatchItem, item.id,
                    status="failed", error=str(e)[:500],
                )
                failed += 1

            _update_record(
                VideoBatchJob, batch_id,
                completed_items=completed, failed_items=failed,
            )

        final_status = "done" if failed == 0 else ("partial" if completed > 0 else "failed")
        _update_record(
            VideoBatchJob, batch_id,
            status=final_status,
            completed_items=completed,
            failed_items=failed,
        )
    finally:
        db.close()


async def render_thumbnail_task(thumbnail_id: int, timeline_json: dict, frame_time: float):
    """Background: render a single frame as a JPEG thumbnail."""
    shotstack = ShotstackService()
    try:
        _update_record(VideoThumbnail, thumbnail_id, status="rendering")

        from shotstack_sdk.model.output import Output

        api_client = shotstack._api_client
        edit_obj = api_client._ApiClient__deserialize(timeline_json, 'Edit')
        edit_obj.output = Output(
            format="jpg",
            resolution="hd",
            fps=1.0,
        )
        edit_obj.output.poster = {"capture": frame_time}

        result = shotstack.submit_render(edit_obj)
        render_id = result["id"]
        _update_record(
            VideoThumbnail, thumbnail_id,
            shotstack_render_id=render_id,
            timeline_json=timeline_json,
        )
        logger.info(f"Thumbnail {thumbnail_id} submitted: {render_id}")

    except Exception as e:
        logger.error(f"Thumbnail {thumbnail_id} failed: {e}")
        _update_record(VideoThumbnail, thumbnail_id, status="failed")
    finally:
        shotstack.close()


async def render_cma_video_task(
    cma_id: int, agent_id: int, property_id: int,
    max_comps: int, include_rentals: bool, style: str,
    background_music_url: Optional[str],
):
    """Background: build CMA video from comps data and render."""
    from app.models.comp_sale import CompSale
    from app.models.comp_rental import CompRental
    from app.models.agentic_property import ResearchProperty

    shotstack = ShotstackService()
    try:
        _update_record(CmaVideo, cma_id, status="loading_data")

        db = SessionLocal()
        try:
            brand = db.query(AgentBrand).filter(AgentBrand.agent_id == agent_id).first()
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            prop = db.query(Property).filter(Property.id == property_id).first()

            if not brand or not agent or not prop:
                raise ValueError("Missing brand, agent, or property")

            research_prop = (
                db.query(ResearchProperty)
                .filter(ResearchProperty.raw_address.ilike(f"%{prop.address}%"))
                .first()
            )

            sale_comps = []
            rental_comps = []
            if research_prop:
                sale_comps = (
                    db.query(CompSale)
                    .filter(CompSale.research_property_id == research_prop.id, CompSale.is_current == True)
                    .order_by(CompSale.sale_date.desc())
                    .limit(max_comps)
                    .all()
                )
                if include_rentals:
                    rental_comps = (
                        db.query(CompRental)
                        .filter(CompRental.research_property_id == research_prop.id, CompRental.is_current == True)
                        .limit(max_comps)
                        .all()
                    )

            primary_color = brand.primary_color or "#1E3A8A"
            text_color = brand.text_color or "#FFFFFF"
            logo_url = brand.logo_url
            preset = STYLE_PRESETS.get(style, STYLE_PRESETS["professional"])

            comp_data = {
                "subject_property": {
                    "address": prop.address,
                    "price": float(prop.price) if prop.price else 0,
                    "beds": prop.bedrooms,
                    "baths": float(prop.bathrooms) if prop.bathrooms else 0,
                    "sqft": prop.square_feet,
                },
                "sale_comps": [
                    {
                        "address": c.address or "Unknown",
                        "sold_price": float(c.sale_price) if c.sale_price else 0,
                        "sold_date": str(c.sale_date) if c.sale_date else "",
                        "beds": c.beds,
                        "baths": float(c.baths) if c.baths else 0,
                        "sqft": c.sqft,
                        "distance_miles": float(c.distance_mi) if c.distance_mi else 0,
                    }
                    for c in sale_comps
                ],
                "rental_comps": [
                    {
                        "address": c.address or "Unknown",
                        "rent": float(c.rent) if c.rent else 0,
                        "beds": c.beds,
                        "baths": float(c.baths) if c.baths else 0,
                    }
                    for c in rental_comps
                ],
            }
        finally:
            db.close()

        _update_record(CmaVideo, cma_id, status="building_timeline", comp_data=comp_data)

        clips_spec = []
        offset = 0.0
        scene_len = preset["scene_length"]

        # Title slide
        title_css = (
            f"font-family:{preset['title_font']};font-size:40px;font-weight:bold;"
            f"color:{text_color};text-align:center;"
        )
        clips_spec.append({
            "type": "html",
            "html": f'<div style="{title_css}">Comparable Market Analysis<br><span style="font-size:24px">{comp_data["subject_property"]["address"]}</span></div>',
            "start": offset,
            "length": scene_len,
            "track": 0,
            "position": "center",
            "width": 800,
            "height": 200,
        })
        offset += scene_len

        # Subject property slide
        subj = comp_data["subject_property"]
        subj_html = (
            f"<b>{subj['address']}</b><br>"
            f"Price: ${subj['price']:,.0f}<br>"
            f"{subj.get('beds', '?')} Bed | {subj.get('baths', '?')} Bath"
        )
        if subj.get("sqft"):
            subj_html += f" | {subj['sqft']:,} sqft"
        body_css = (
            f"font-family:{preset['body_font']};font-size:28px;"
            f"color:{text_color};background:rgba({_hex_to_rgb(primary_color)},0.80);"
            f"padding:16px 32px;border-radius:8px;text-align:center;"
        )
        clips_spec.append({
            "type": "html",
            "html": f'<div style="{body_css}">{subj_html}</div>',
            "start": offset,
            "length": scene_len,
            "track": 0,
            "position": "center",
            "width": 800,
            "height": 200,
        })
        offset += scene_len

        # Each comp slide
        for i, comp in enumerate(comp_data["sale_comps"]):
            comp_html = (
                f"<b>Comp #{i+1}: {comp['address']}</b><br>"
                f"Sold: ${comp['sold_price']:,.0f}"
            )
            if comp.get("sold_date"):
                comp_html += f" ({comp['sold_date'][:10]})"
            comp_html += f"<br>{comp.get('beds', '?')} Bed | {comp.get('baths', '?')} Bath"
            if comp.get("sqft"):
                comp_html += f" | {comp['sqft']:,} sqft"
            if comp.get("distance_miles"):
                comp_html += f"<br>{comp['distance_miles']:.1f} mi away"

            clips_spec.append({
                "type": "html",
                "html": f'<div style="{body_css}">{comp_html}</div>',
                "start": offset,
                "length": scene_len,
                "track": 0,
                "position": "center",
                "width": 800,
                "height": 220,
            })
            offset += scene_len

        # Rental comps
        for i, comp in enumerate(comp_data.get("rental_comps", [])):
            r_html = (
                f"<b>Rental Comp #{i+1}: {comp['address']}</b><br>"
                f"Rent: ${comp['rent']:,.0f}/mo<br>"
                f"{comp.get('beds', '?')} Bed | {comp.get('baths', '?')} Bath"
            )
            clips_spec.append({
                "type": "html",
                "html": f'<div style="{body_css}">{r_html}</div>',
                "start": offset,
                "length": scene_len,
                "track": 0,
                "position": "center",
                "width": 800,
                "height": 180,
            })
            offset += scene_len

        # Summary slide
        if comp_data["sale_comps"]:
            avg_price = sum(c["sold_price"] for c in comp_data["sale_comps"]) / len(comp_data["sale_comps"])
            summary_html = (
                f"<b>Market Summary</b><br>"
                f"Avg Comp Price: ${avg_price:,.0f}<br>"
                f"Subject Price: ${subj['price']:,.0f}<br>"
                f"Based on {len(comp_data['sale_comps'])} comparable sales"
            )
            clips_spec.append({
                "type": "html",
                "html": f'<div style="{body_css}">{summary_html}</div>',
                "start": offset,
                "length": scene_len + 2,
                "track": 0,
                "position": "center",
                "width": 800,
                "height": 200,
            })
            offset += scene_len + 2

        # Logo watermark
        if logo_url:
            clips_spec.append({
                "type": "image",
                "src": logo_url,
                "start": 0,
                "length": offset,
                "track": 0,
                "position": "topRight",
                "scale": 0.12,
                "offset_x": -0.03,
                "offset_y": -0.03,
                "opacity": 0.8,
                "fit": "none",
            })

        # Contact info on last slide
        agent_name = agent.name
        contact_parts = [p for p in [agent_name, brand.display_phone, brand.display_email] if p]
        if contact_parts:
            cta_css = (
                f"font-family:Arial,sans-serif;font-size:22px;color:{text_color};"
                f"text-align:center;line-height:1.6;"
            )
            clips_spec.append({
                "type": "html",
                "html": f'<div style="{cta_css}">{"<br>".join(contact_parts)}</div>',
                "start": max(0, offset - scene_len - 2),
                "length": scene_len + 2,
                "track": 0,
                "position": "bottom",
                "offset_y": -0.08,
                "width": 600,
                "height": 120,
            })

        edit = shotstack.build_custom_timeline(
            clips_spec,
            background=primary_color,
            soundtrack_url=background_music_url,
            soundtrack_volume=0.12,
        )

        _update_record(CmaVideo, cma_id, status="rendering", timeline_json=edit.to_dict(), duration=offset)
        render_result = shotstack.submit_render(edit)
        render_id = render_result["id"]
        _update_record(CmaVideo, cma_id, shotstack_render_id=render_id)
        logger.info(f"CMA video {cma_id} submitted: {render_id}")

    except Exception as e:
        logger.error(f"CMA video {cma_id} failed: {e}")
        _update_record(CmaVideo, cma_id, status="failed", error=str(e)[:500])
    finally:
        shotstack.close()


async def render_listing_slideshow_task(slideshow_id: int, agent_id: int):
    """Background: build slideshow timeline and submit to Shotstack."""
    shotstack = ShotstackService()
    try:
        _update_record(ListingSlideshow, slideshow_id, status="building_timeline")

        db = SessionLocal()
        try:
            ss = db.query(ListingSlideshow).filter(ListingSlideshow.id == slideshow_id).first()
            brand = db.query(AgentBrand).filter(AgentBrand.agent_id == agent_id).first()
            agent = db.query(Agent).filter(Agent.id == agent_id).first()

            if not ss or not brand or not agent:
                raise ValueError("Missing slideshow, brand, or agent data")

            photo_urls = ss.photo_urls or []
            primary_color = brand.primary_color or "#1E3A8A"
            text_color = brand.text_color or "#FFFFFF"
            logo_url = brand.logo_url
            preset = STYLE_PRESETS.get(ss.style, STYLE_PRESETS["professional"])
            ar = ASPECT_RATIOS.get(ss.aspect_ratio, ASPECT_RATIOS["16:9"])
            sec_per = ss.seconds_per_photo or 4.0
            title_text = ss.title_text or ""
            subtitle_text = ss.subtitle_text or ""
            cta_text = ss.cta_text or ""
            agent_name = agent.name
        finally:
            db.close()

        clips_spec = []
        offset = 0.0

        for i, url in enumerate(photo_urls):
            clips_spec.append({
                "type": "image",
                "src": url,
                "start": offset,
                "length": sec_per,
                "track": 1,
                "fit": "cover",
                "effect": "zoomInSlow" if i % 2 == 0 else "zoomOutSlow",
                "transition_in": preset["transition_in"],
                "transition_out": preset["transition_out"],
            })

            if i == 0 and title_text:
                title_css = (
                    f"font-family:{preset['title_font']};font-size:{preset['title_size']}px;"
                    f"font-weight:bold;color:{text_color};"
                    f"background:rgba({_hex_to_rgb(primary_color)},{preset['text_bg_opacity']});"
                    f"padding:{preset['text_padding']};border-radius:{preset['text_border_radius']}px;"
                    f"text-align:center;letter-spacing:{preset['text_letter_spacing']};"
                    f"text-transform:{preset['text_transform']};"
                )
                clips_spec.append({
                    "type": "html",
                    "html": f'<div style="{title_css}">{title_text}</div>',
                    "start": offset,
                    "length": sec_per,
                    "track": 0,
                    "position": "bottom",
                    "offset_y": -0.05,
                    "width": int(ar["width"] * 0.85),
                    "height": 120,
                })

            elif i == 1 and subtitle_text:
                sub_css = (
                    f"font-family:{preset['body_font']};font-size:{preset['body_size']}px;"
                    f"color:{text_color};"
                    f"background:rgba({_hex_to_rgb(primary_color)},{preset['text_bg_opacity']});"
                    f"padding:{preset['text_padding']};border-radius:{preset['text_border_radius']}px;"
                    f"text-align:center;"
                )
                clips_spec.append({
                    "type": "html",
                    "html": f'<div style="{sub_css}">{subtitle_text}</div>',
                    "start": offset,
                    "length": sec_per,
                    "track": 0,
                    "position": "bottom",
                    "offset_y": -0.05,
                    "width": int(ar["width"] * 0.85),
                    "height": 100,
                })

            offset += sec_per

        # CTA / contact on last slide
        contact_parts = [p for p in [agent_name, brand.display_phone, brand.display_email] if p]
        if cta_text:
            contact_parts.insert(0, f"<b>{cta_text}</b>")
        if contact_parts:
            cta_css = (
                f"font-family:Arial,sans-serif;font-size:24px;color:{text_color};"
                f"background:rgba({_hex_to_rgb(primary_color)},0.85);"
                f"padding:12px 24px;border-radius:8px;text-align:center;line-height:1.5;"
            )
            cta_start = max(0, offset - sec_per)
            clips_spec.append({
                "type": "html",
                "html": f'<div style="{cta_css}">{"<br>".join(contact_parts)}</div>',
                "start": cta_start,
                "length": sec_per,
                "track": 0,
                "position": "center",
                "offset_y": 0.1,
                "width": int(ar["width"] * 0.8),
                "height": 160,
                "transition_in": "fade",
            })

        # Logo watermark throughout
        if logo_url:
            clips_spec.append({
                "type": "image",
                "src": logo_url,
                "start": 0,
                "length": offset,
                "track": 0,
                "position": "topRight",
                "scale": preset["logo_scale"],
                "offset_x": -0.03,
                "offset_y": -0.03,
                "opacity": 0.85,
                "fit": "none",
            })

        edit = shotstack.build_custom_timeline(
            clips_spec,
            background="#000000",
            soundtrack_url=ss.background_music_url,
            soundtrack_volume=preset["music_volume"],
        )

        from shotstack_sdk.model.output import Output
        from shotstack_sdk.model.size import Size
        edit.output = Output(
            format="mp4",
            resolution=ar["resolution"],
            fps=float(preset["output_fps"]),
            size=Size(width=ar["width"], height=ar["height"]),
        )

        _update_record(ListingSlideshow, slideshow_id, status="rendering", timeline_json=edit.to_dict(), duration=offset)
        render_result = shotstack.submit_render(edit)
        render_id = render_result["id"]
        _update_record(ListingSlideshow, slideshow_id, shotstack_render_id=render_id)
        logger.info(f"Slideshow {slideshow_id} submitted: {render_id}")

    except Exception as e:
        logger.error(f"Slideshow {slideshow_id} failed: {e}")
        _update_record(ListingSlideshow, slideshow_id, status="failed", error=str(e)[:500])
    finally:
        shotstack.close()


# ======================================================================
# Dependency injection
# ======================================================================

def get_shotstack_enhanced_service(db: Session = Depends(get_db)) -> ShotstackEnhancedService:
    return ShotstackEnhancedService(db)
