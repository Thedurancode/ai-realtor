"""Enhanced Property Video Service

Orchestrates complete property video generation pipeline.
Coordinates script generation, voiceover, avatar videos, property footage, and assembly.
"""
import logging
from typing import Dict, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.property import Property
from app.models.agent_video_profile import AgentVideoProfile
from app.models.property_video import PropertyVideo, VideoTypeEnum, VideoGenerationStatus
# D-ID service for talking head videos
from app.services.did_service import DIDService
# PixVerse for property footage (optional)
from app.services.pixverse_service import PixVerseService
from app.services.script_generator_enhanced import ScriptGeneratorService
from app.services.video_assembler import VideoAssemblerService

logger = logging.getLogger(__name__)


class EnhancedPropertyVideoService:
    """
    Orchestrate complete property video generation.

    Pipeline:
    1. Generate script (Claude AI)
    2. Generate voiceover (ElevenLabs)
    3. Generate avatar intro (HeyGen)
    4. Generate property footage (PixVerse)
    5. Generate avatar outro (HeyGen)
    6. Assemble final video (FFmpeg)
    7. Upload to S3
    """

    def __init__(self, db: Session):
        self.db = db
        # D-ID for talking heads (optional - may not be configured)
        self.did = DIDService()
        # PixVerse for AI footage (optional - may not be configured)
        try:
            self.pixverse = PixVerseService()
        except:
            self.pixverse = None
        self.script_generator = ScriptGeneratorService()
        self.video_assembler = VideoAssemblerService()

    async def generate_property_video(
        self,
        property_id: int,
        agent_id: int,
        video_type: VideoTypeEnum = VideoTypeEnum.PROPERTY_TOUR,
        style: str = "luxury",
        duration_target: int = 60
    ) -> PropertyVideo:
        """
        Generate complete property video with agent avatar.

        Args:
            property_id: Property ID
            agent_id: Agent ID
            video_type: Type of video
            style: Video style (luxury, friendly, professional)
            duration_target: Target duration in seconds

        Returns:
            PropertyVideo record with all URLs and metadata

        Raises:
            Exception: If generation fails at any step
        """
        logger.info(f"Starting property video generation for property {property_id}")

        # Step 1: Get data
        property_data = await self._get_property_data(property_id, agent_id)
        agent_profile = await self._get_agent_video_profile(agent_id)

        # Create video record
        video = PropertyVideo(
            agent_id=agent_id,
            property_id=property_id,
            video_type=video_type,
            style=style,
            duration_target=duration_target,
            status=VideoGenerationStatus.DRAFT
        )
        self.db.add(video)
        self.db.commit()
        self.db.refresh(video)

        try:
            # Step 2: Generate script
            self._update_status(video, VideoGenerationStatus.GENERATING_SCRIPT)
            script = await self.script_generator.generate_property_script(
                property_data=property_data,
                style=style,
                duration=duration_target
            )
            # Serialize script to JSON for database storage
            import json
            video.generated_script = json.dumps(script)
            self._update_status(video, VideoGenerationStatus.SCRIPT_COMPLETED)
            logger.info("Script generated successfully")

            # Step 3: Generate voiceover
            self._update_status(video, VideoGenerationStatus.GENERATING_VOICEOVER)
            voiceover_url = await self._generate_voiceover(
                script=script["property_highlights"],
                voice_id=agent_profile.voice_id
            )
            video.voiceover_url = voiceover_url
            self._update_status(video, VideoGenerationStatus.VOICEOVER_COMPLETED)
            logger.info("Voiceover generated successfully")

            # Step 4: Generate avatar intro
            self._update_status(video, VideoGenerationStatus.GENERATING_INTRO)
            intro_video_url = None
            try:
                intro_script = agent_profile.default_intro_script or script["agent_intro"]
                intro_video_url = await self._generate_avatar_video(
                    headshot_url=agent_profile.headshot_url,
                    script=intro_script,
                    voice_id=agent_profile.voice_id,
                    background_color=agent_profile.background_color
                )
                video.intro_video_url = intro_video_url
                logger.info("Avatar intro generated successfully")
            except Exception as e:
                logger.warning(f"Avatar intro generation failed, continuing without it: {str(e)}")
                video.intro_video_url = None

            self._update_status(video, VideoGenerationStatus.INTRO_COMPLETED)

            # Step 5: Generate property footage
            self._update_status(video, VideoGenerationStatus.GENERATING_FOOTAGE)
            photos = self._select_property_photos(property_data, max_photos=5)
            property_clips = await self._generate_property_footage(
                photo_urls=photos,
                property_data=property_data,
                style=style
            )
            video.property_clips = [clip["video_url"] for clip in property_clips if clip.get("status") == "succeeded"]
            video.photos_used = photos
            self._update_status(video, VideoGenerationStatus.FOOTAGE_COMPLETED)
            logger.info(f"Generated {len(video.property_clips)} property clips")

            # Step 6: Generate avatar outro
            outro_video_url = None
            try:
                outro_script = agent_profile.default_outro_script or script["call_to_action"]
                outro_video_url = await self._generate_avatar_video(
                    headshot_url=agent_profile.headshot_url,
                    script=outro_script,
                    voice_id=agent_profile.voice_id,
                    background_color=agent_profile.background_color
                )
                video.outro_video_url = outro_video_url
                logger.info("Avatar outro generated successfully")
            except Exception as e:
                logger.warning(f"Avatar outro generation failed, continuing without it: {str(e)}")
                video.outro_video_url = None

            # Step 7: Assemble final video
            self._update_status(video, VideoGenerationStatus.ASSEMBLING_VIDEO)
            output_filename = f"property_{property_id}_{int(datetime.now(timezone.utc).timestamp())}.mp4"

            assembly_result = await self.video_assembler.assemble_property_video(
                intro_video_url=intro_video_url,
                property_clips=video.property_clips,
                outro_video_url=outro_video_url,
                voiceover_url=voiceover_url,
                output_filename=output_filename,
                property_photos=video.photos_used,
                agent_headshot_url=agent_profile.headshot_url
            )

            video.final_video_url = assembly_result["final_video_url"]
            video.thumbnail_url = assembly_result["thumbnail_url"]
            video.duration = assembly_result["duration"]
            video.resolution = assembly_result["resolution"]
            video.file_size = assembly_result["file_size"]

            # Step 8: Update status and costs
            video.status = VideoGenerationStatus.COMPLETED
            video.completed_at = datetime.now(timezone.utc)
            video.generation_cost = await self._calculate_total_cost(video)
            video.cost_breakdown = await self._calculate_cost_breakdown(video)

            self.db.commit()
            logger.info(f"Property video generation complete: {video.final_video_url}")

            return video

        except Exception as e:
            logger.error(f"Video generation failed: {str(e)}")
            video.status = VideoGenerationStatus.FAILED
            video.error_message = str(e)
            self.db.commit()
            raise

    async def _get_property_data(self, property_id: int, agent_id: int = None) -> Dict:
        """Get property data for script generation."""
        property = self.db.query(Property).filter(Property.id == property_id).first()
        if not property:
            raise ValueError(f"Property {property_id} not found")

        # Get Zillow enrichment if available
        enrichment = property.zillow_enrichment

        # Extract photos from enrichment or use empty array
        photos = []
        if enrichment and enrichment.photos:
            photos = enrichment.photos if isinstance(enrichment.photos, list) else []

        # Get agent information if agent_id provided
        agent_info = {}
        if agent_id:
            from app.models.agent import Agent
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            if agent:
                agent_info = {
                    "agent_name": agent.name,
                    "agent_email": agent.email,
                    "agent_phone": agent.phone,
                }

                # Try to get company name from onboarding or brand
                if agent.onboarding and agent.onboarding.business_name:
                    agent_info["agent_company"] = agent.onboarding.business_name
                elif agent.brand and agent.brand.company_name:
                    agent_info["agent_company"] = agent.brand.company_name
                else:
                    agent_info["agent_company"] = "Emprezario Inc"  # Default

        # Handle property_type (could be enum or string)
        property_type_value = "house"
        if property.property_type:
            if hasattr(property.property_type, 'value'):
                property_type_value = property.property_type.value
            else:
                property_type_value = str(property.property_type)

        return {
            "address": property.address,
            "city": property.city,
            "state": property.state,
            "zip_code": property.zip_code,
            "price": property.price,
            "bedrooms": property.bedrooms,
            "bathrooms": property.bathrooms,
            "square_feet": property.square_feet or 0,
            "property_type": property_type_value,
            "description": enrichment.description if enrichment else property.description or "",
            "year_built": enrichment.year_built if enrichment else None,
            "photos": photos,
            **agent_info  # Include agent information
        }

    async def _get_agent_video_profile(self, agent_id: int) -> AgentVideoProfile:
        """Get agent video profile for avatar/voice settings."""
        profile = self.db.query(AgentVideoProfile).filter(
            AgentVideoProfile.agent_id == agent_id
        ).first()

        if not profile:
            raise ValueError(
                f"Agent video profile not found for agent {agent_id}. "
                "Please create a profile with avatar and voice settings."
            )

        return profile

    async def _generate_voiceover(self, script: str, voice_id: str) -> str:
        """Generate voiceover using ElevenLabs."""
        from elevenlabs import ElevenLabs
        import tempfile
        import os
        from app.config import settings

        # Get API key from settings (loads from .env)
        api_key = settings.elevenlabs_api_key
        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY not configured in settings")

        # Generate audio using ElevenLabs
        client = ElevenLabs(api_key=api_key)

        try:
            # Generate speech
            audio_generator = client.text_to_speech.convert(
                text=script,
                voice_id=voice_id,
                model_id="eleven_multilingual_v2"
            )

            # Convert generator to bytes
            audio_bytes = b""
            for chunk in audio_generator:
                audio_bytes += chunk

            # Save to temp file and return path
            # In production, upload to S3 and return URL
            fd, audio_path = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)
            with open(audio_path, "wb") as f:
                f.write(audio_bytes)

            return audio_path

        except Exception as e:
            logger.error(f"Voiceover generation failed: {str(e)}")
            raise

    async def _generate_avatar_video(
        self,
        headshot_url: str,
        script: str,
        voice_id: str,
        background_color: str
    ) -> str:
        """Generate talking head video using D-ID."""
        logger.info(f"Creating D-ID talking head video from {headshot_url}")

        # Convert ElevenLabs voice_id to D-ID voice_id format
        # D-ID uses format like "en-US-Jenny" for ElevenLabs voices
        did_voice_id = voice_id  # D-ID uses similar voice IDs

        result = await self.did.create_talking_head(
            image_url=headshot_url,
            script=script,
            voice_id=did_voice_id,
            background_color=background_color
        )

        video_id = result["video_id"]

        # Wait for completion
        logger.info(f"Waiting for D-ID video {video_id} to complete...")
        completed = await self.did.wait_for_video(video_id, timeout=600)

        video_url = completed.get("result_url")
        if not video_url:
            raise Exception(f"D-ID video completed but no result_url found")

        # Download and save locally
        video_content = await self.did.download_video(video_url)

        # Save to local filesystem
        import tempfile
        import os
        fd, temp_path = tempfile.mkstemp(suffix=".mp4")
        os.close(fd)
        with open(temp_path, "wb") as f:
            f.write(video_content)

        logger.info(f"D-ID video saved to {temp_path}")
        return temp_path  # Return local path for assembly

    async def _generate_property_footage(
        self,
        photo_urls: list,
        property_data: Dict,
        style: str
    ) -> list:
        """Generate property footage using PixVerse."""
        prompt = await self.pixverse.get_property_footage_prompts(property_data, style)

        return await self.pixverse.batch_generate_clips(
            photo_urls=photo_urls,
            prompt=prompt,
            duration=8,
            resolution="1080p",
            camera_movement="pan_right",
            concurrent=3
        )

    def _select_property_photos(self, property_data: Dict, max_photos: int = 5) -> list:
        """Select best property photos for video."""
        photos = property_data.get("photos", [])

        if not photos:
            raise ValueError("No photos available for this property")

        return photos[:max_photos]

    def _update_status(self, video: PropertyVideo, status: VideoGenerationStatus):
        """Update video status and track generation steps."""
        video.status = status.value

        if not video.generation_steps:
            video.generation_steps = []

        video.generation_steps.append({
            "step": status.value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        self.db.commit()

    async def _calculate_total_cost(self, video: PropertyVideo) -> float:
        """Calculate total generation cost."""
        breakdown = await self._calculate_cost_breakdown(video)
        return sum(breakdown.values())

    async def _calculate_cost_breakdown(self, video: PropertyVideo) -> Dict:
        """Calculate cost breakdown by component."""
        breakdown = {}

        # D-ID talking heads (only if actually generated)
        if video.intro_video_url and "d-id" in video.intro_video_url.lower():
            breakdown["d_id_intro"] = 1.00  # ~$1 per video
        if video.outro_video_url and "d-id" in video.outro_video_url.lower():
            breakdown["d_id_outro"] = 1.00

        # PixVerse AI footage (only if succeeded)
        num_clips = len([c for c in video.property_clips or [] if c])
        if num_clips > 0:
            breakdown["pixverse_footage"] = num_clips * 0.02

        # ElevenLabs voiceover
        if video.voiceover_url:
            breakdown["elevenlabs_voiceover"] = 0.03

        # Assembly (FFmpeg processing + storage)
        breakdown["assembly"] = 0.02

        return breakdown

    async def close(self):
        """Close service connections."""
        if hasattr(self, 'did') and self.did:
            await self.did.close()
        if hasattr(self, 'pixverse') and self.pixverse:
            await self.pixverse.close()


# ============================================================================
# Helper Functions
# ============================================================================

async def generate_video_for_property(
    property_id: int,
    agent_id: int,
    style: str = "luxury",
    duration: int = 60,
    db: Session = None
) -> PropertyVideo:
    """
    Convenience function to generate property video.

    Args:
        property_id: Property ID
        agent_id: Agent ID
        style: Video style
        duration: Target duration
        db: Database session

    Returns:
        Generated PropertyVideo record
    """
    if not db:
        from app.database import SessionLocal
        db = SessionLocal()

    service = EnhancedPropertyVideoService(db)
    try:
        return await service.generate_property_video(
            property_id=property_id,
            agent_id=agent_id,
            style=style,
            duration_target=duration
        )
    finally:
        await service.close()
