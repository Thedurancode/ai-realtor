"""VideoGen AI Avatar Video Generation Service

Generate AI avatar videos using HeyGen API and integrate with social media.
"""
import os
import tempfile
import logging
from typing import Dict, Optional, List
from datetime import datetime, timezone
import httpx
import asyncio

logger = logging.getLogger(__name__)


class VideoGenService:
    """Service for generating AI avatar videos"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("VIDEOGEN_API_KEY")
        self.base_url = "https://api.heygen.com"
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    async def list_avatars(self) -> List[Dict]:
        """Get available AI avatars

        Returns:
            List of avatars with id, name, preview_url, gender, etc.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/v2/avatars",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", {}).get("avatars", [])

    async def generate_video(
        self,
        script: str,
        avatar_id: str,
        voice_id: Optional[str] = None,
        background: str = "#FFFFFF",
        aspect_ratio: str = "16:9",
        test: bool = False
    ) -> Dict:
        """Generate avatar video from script

        Args:
            script: Text for avatar to speak
            avatar_id: VideoGen avatar ID
            voice_id: Optional voice ID (default avatar voice)
            background: Background color (hex)
            aspect_ratio: 16:9 (landscape) or 9:16 (portrait for TikTok/Reels)
            test: If True, returns test response without generating

        Returns:
            {
                "video_id": "abc123",
                "status": "processing",
                "estimated_time": 120
            }
        """
        if test:
            # Return mock response for testing
            return {
                "error": None,
                "data": {
                    "video_id": "test_video_123",
                    "status": "processing",
                    "estimated_time": 120
                }
            }

        payload = {
            "avatar": avatar_id,
            "voice": {
                "type": "text",
                "input_text": script
            },
            "background": background,
            "aspect_ratio": aspect_ratio
        }

        if voice_id:
            payload["voice"]["voice_id"] = voice_id

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/video.generate",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

    async def get_video_status(self, video_id: str) -> Dict:
        """Check video generation status

        Args:
            video_id: Video ID from generate_video

        Returns:
            {
                "data": {
                    "video_id": "abc123",
                    "status": "completed" | "processing" | "failed",
                    "video_url": "https://..."
                }
            }
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/v1/video.status",
                headers=self.headers,
                params={"video_id": video_id}
            )
            response.raise_for_status()
            return response.json()

    async def wait_for_video(
        self,
        video_id: str,
        timeout: int = 300,
        check_interval: int = 10
    ) -> Dict:
        """Wait for video to complete processing

        Args:
            video_id: Video ID to wait for
            timeout: Maximum seconds to wait
            check_interval: Seconds between status checks

        Returns:
            Video data with video_url when complete

        Raises:
            TimeoutError: If video doesn't complete in time
            Exception: If video generation fails
        """
        start_time = datetime.now(timezone.utc)

        while True:
            elapsed = (datetime.now(timezone.utc) - start_time).seconds

            if elapsed > timeout:
                raise TimeoutError(f"Video processing timeout after {timeout}s")

            status_response = await self.get_video_status(video_id)
            status_data = status_response.get("data", {})
            status = status_data.get("status")

            logger.info(f"Video {video_id} status: {status} ({elapsed}s elapsed)")

            if status == "completed":
                logger.info(f"Video {video_id} completed successfully")
                return status_data

            if status == "failed":
                error_msg = status_data.get("error", "Unknown error")
                raise Exception(f"Video generation failed: {error_msg}")

            await asyncio.sleep(check_interval)

    async def download_video(self, video_url: str) -> bytes:
        """Download video from URL

        Args:
            video_url: URL to download from

        Returns:
            Video content as bytes
        """
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(video_url)
            response.raise_for_status()
            return response.content

    async def generate_property_script(
        self,
        property_data: Dict,
        script_type: str = "promotion"
    ) -> str:
        """Generate video script from property data

        Args:
            property_data: Property details dict
            script_type: Type of script (promotion, market_update, open_house)

        Returns:
            Generated script text
        """
        if script_type == "promotion":
            return f"""
Welcome to this stunning property in {property_data.get('city', 'a great location')}!

This beautiful {property_data.get('property_type', 'home')} features
{property_data.get('bedrooms', 'spacious')} bedrooms and
{property_data.get('bathrooms', 'modern')} bathrooms.

With {property_data.get('square_footage', 'ample')} square feet of living space,
this home offers plenty of room to relax and entertain.

Priced at {property_data.get('price', 'a great value')},
this property won't last long!

Contact us today to schedule your private tour.
            """.strip()

        elif script_type == "open_house":
            return f"""
You're invited to our exclusive open house!

Join us this weekend to tour this amazing property in {property_data.get('city', 'a great location')}.

Features include:
{property_data.get('bedrooms', 'Multiple')} bedrooms
{property_data.get('bathrooms', 'Multiple')} bathrooms
{property_data.get('square_footage', 'Spacious')} square feet

Refreshments will be provided!

We can't wait to see you there.
            """.strip()

        elif script_type == "market_update":
            return f"""
📊 Market Update for {property_data.get('city', 'Your Area')}!

The real estate market is active right now.

Whether you're buying or selling, this is a great time to make your move.

Contact me for a free market analysis of your property.

I'm here to help you navigate the market with confidence.
            """.strip()

        else:
            return "Check out this amazing property opportunity!"

    async def list_voices(self) -> List[Dict]:
        """Get available text-to-speech voices

        Returns:
            List of voices with id, name, language, gender
        """
        # This would call the actual API if available
        # For now, return common voices
        return [
            {"voice_id": "default", "name": "Default Voice", "language": "en-US", "gender": "female"},
            {"voice_id": "anna", "name": "Anna", "language": "en-US", "gender": "female"},
            {"voice_id": "josh", "name": "Josh", "language": "en-US", "gender": "male"},
        ]


# ============================================================================
# Helper Functions
# ============================================================================

async def generate_video_and_upload(
    script: str,
    avatar_id: str,
    agent_id: int,
    db,
    aspect_ratio: str = "16:9",
    platforms: Optional[List[str]] = None
) -> Dict:
    """Generate video and upload to Postiz

    This is a convenience function that combines:
    1. Generate video with VideoGen
    2. Wait for processing
    3. Download video
    4. Upload to Postiz

    Args:
        script: Video script
        avatar_id: Avatar to use
        agent_id: Agent ID for Postiz upload
        db: Database session
        aspect_ratio: Video aspect ratio
        platforms: Platforms to optimize for

    Returns:
        {
            "video_id": "...",
            "video_url": "...",
            "postiz_media_id": "...",
            "postiz_media_url": "..."
        }
    """
    from app.services.postiz_service import PostizService

    videogen = VideoGenService()
    postiz = PostizService(db)

    # Step 1: Generate video
    logger.info("Generating VideoGen video...")
    gen_response = await videogen.generate_video(
        script=script,
        avatar_id=avatar_id,
        aspect_ratio=aspect_ratio
    )

    video_data = gen_response.get("data", {})
    video_id = video_data.get("video_id")

    if not video_id:
        raise Exception("Failed to generate video: No video_id returned")

    logger.info(f"Video {video_id} generated, waiting for processing...")

    # Step 2: Wait for processing
    completed_video = await videogen.wait_for_video(video_id, timeout=300)
    video_url = completed_video.get("video_url")

    if not video_url:
        raise Exception("Video completed but no URL returned")

    logger.info(f"Video ready: {video_url}")

    # Step 3: Download video
    logger.info("Downloading video...")
    video_content = await videogen.download_video(video_url)

    # Step 4: Upload to Postiz
    logger.info("Uploading to Postiz...")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(video_content)
        tmp_path = tmp.name

    try:
        media_result = await postiz.upload_media(agent_id, file_path=tmp_path)
        logger.info(f"Uploaded to Postiz: {media_result.get('id')}")
    finally:
        import os
        os.unlink(tmp_path)

    return {
        "videogen_video_id": video_id,
        "video_url": video_url,
        "postiz_media_id": media_result.get("id"),
        "postiz_media_url": media_result.get("path"),
        "platforms": platforms or []
    }
