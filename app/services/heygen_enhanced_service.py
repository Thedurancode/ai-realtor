"""HeyGen Enhanced Service

Extended HeyGen API integration for custom avatar creation and video generation.
Builds on existing videogen_service.py with additional features.
"""
import os
import logging
from typing import Dict, Optional
from datetime import datetime, timezone
import httpx
import asyncio

from app.config import settings

logger = logging.getLogger(__name__)


class HeyGenEnhancedService:
    """
    Enhanced HeyGen service with custom avatar creation and advanced features.

    Extends the base VideoGenService with:
    - Custom avatar creation from agent photos
    - Enhanced video generation with branding
    - Better error handling and retries
    """

    BASE_URL = "https://api.heygen.com"
    API_VERSION = "v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.heygen_api_key
        if not self.api_key:
            logger.warning("HeyGen API key not configured")

        self.client = httpx.AsyncClient(
            base_url=f"{self.BASE_URL}",
            headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/json"
            },
            timeout=120.0  # 2 minute timeout
        )

    async def create_custom_avatar(
        self,
        agent_id: int,
        photo_url: str,
        name: str,
        gender: str = "female"
    ) -> Dict:
        """
        Create a custom avatar from agent's headshot photo.

        Args:
            agent_id: Agent ID for tracking
            photo_url: URL to agent's headshot photo
            name: Avatar name (e.g., "Jane_Smith_Realtor")
            gender: "male" or "female" for voice matching

        Returns:
            {
                "avatar_id": "custom_abc123",
                "status": "processing",
                "preview_url": "https://..."
            }

        Raises:
            Exception: If avatar creation fails
        """
        logger.info(f"Creating custom avatar for agent {agent_id} from {photo_url}")

        try:
            response = await self.client.post(
                f"/{self.API_VERSION}/avatars.create_instant_avatar",
                json={
                    "avatar_name": name,
                    "avatar_type": "instant",
                    "image": photo_url,
                    "gender": gender
                }
            )
            response.raise_for_status()
            result = response.json()

            avatar_id = result.get("data", {}).get("avatar_id")
            logger.info(f"Custom avatar creation started: {avatar_id}")

            return {
                "avatar_id": avatar_id,
                "status": "processing",
                "preview_url": result.get("data", {}).get("preview_image_url")
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"HeyGen API error: {e.response.text}")
            raise Exception(f"Failed to create custom avatar: {e.response.text}")
        except Exception as e:
            logger.error(f"Avatar creation error: {str(e)}")
            raise

    async def check_avatar_status(self, avatar_id: str) -> Dict:
        """
        Check custom avatar creation status.

        Args:
            avatar_id: Custom avatar ID

        Returns:
            {
                "avatar_id": "custom_abc123",
                "status": "completed" | "processing" | "failed",
                "preview_url": "https://..."
            }
        """
        try:
            response = await self.client.get(
                f"/{self.API_VERSION}/avatars.status",
                params={"avatar_id": avatar_id}
            )
            response.raise_for_status()
            return response.json().get("data", {})

        except Exception as e:
            logger.error(f"Failed to check avatar status: {str(e)}")
            raise

    async def generate_talking_head(
        self,
        avatar_id: str,
        script: str,
        voice_id: Optional[str] = None,
        background_color: str = "#f8fafc",
        aspect_ratio: str = "16:9",
        resolution: str = "1080p"
    ) -> Dict:
        """
        Generate talking head video from avatar and script.

        Args:
            avatar_id: HeyGen avatar ID (custom or pre-made)
            script: Text for avatar to speak
            voice_id: Optional ElevenLabs voice ID
            background_color: Background hex color
            aspect_ratio: "16:9" (landscape) or "9:16" (portrait)
            resolution: "720p", "1080p", or "4k"

        Returns:
            {
                "video_id": "abc123",
                "status": "processing",
                "estimated_time": 120
            }
        """
        logger.info(f"Generating talking head video with avatar {avatar_id}")

        payload = {
            "avatar": {
                "type": "custom" if avatar_id.startswith("custom_") else "public",
                "avatar_id": avatar_id
            },
            "voice": {
                "type": "text",
                "input_text": script
            },
            "background": {
                "type": "color",
                "value": background_color
            },
            "aspect_ratio": aspect_ratio,
            "resolution": resolution
        }

        # Add custom voice if provided
        if voice_id:
            payload["voice"]["voice_id"] = voice_id

        try:
            response = await self.client.post(
                f"/{self.API_VERSION}/video.generate",
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            video_id = result.get("data", {}).get("video_id")
            logger.info(f"Video generation started: {video_id}")

            return {
                "video_id": video_id,
                "status": "processing",
                "estimated_time": result.get("data", {}).get("estimated_time", 120)
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"HeyGen API error: {e.response.text}")
            raise Exception(f"Video generation failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Video generation error: {str(e)}")
            raise

    async def get_video_status(self, video_id: str) -> Dict:
        """
        Check video generation status.

        Args:
            video_id: Video ID from generate_talking_head

        Returns:
            {
                "video_id": "abc123",
                "status": "completed" | "processing" | "failed",
                "video_url": "https://...",
                "duration": 45.2,
                "error": "..."  # if failed
            }
        """
        try:
            response = await self.client.get(
                f"/{self.API_VERSION}/video.status",
                params={"video_id": video_id}
            )
            response.raise_for_status()
            return response.json().get("data", {})

        except Exception as e:
            logger.error(f"Failed to check video status: {str(e)}")
            raise

    async def wait_for_video(
        self,
        video_id: str,
        timeout: int = 600,
        check_interval: int = 10
    ) -> Dict:
        """
        Wait for video to complete processing.

        Args:
            video_id: Video ID to wait for
            timeout: Maximum seconds to wait (default 10 min)
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

            status_data = await self.get_video_status(video_id)
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
        """
        Download video from URL.

        Args:
            video_url: URL to download from

        Returns:
            Video content as bytes
        """
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.get(video_url)
            response.raise_for_status()
            return response.content

    async def list_available_voices(self) -> list:
        """
        List available text-to-speech voices.

        Returns:
            List of voice dictionaries with id, name, language, gender
        """
        try:
            response = await self.client.get(f"/{self.API_VERSION}/voices")
            response.raise_for_status()
            return response.json().get("data", {}).get("voices", [])

        except Exception as e:
            logger.error(f"Failed to list voices: {str(e)}")
            # Return default voices if API fails
            return [
                {"voice_id": "en-US-Jenny", "name": "Jenny", "language": "en-US", "gender": "female"},
                {"voice_id": "en-US-Joe", "name": "Joe", "language": "en-US", "gender": "male"},
            ]

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# ============================================================================
# Helper Functions
# ============================================================================

async def create_agent_avatar(
    agent_id: int,
    photo_url: str,
    agent_name: str,
    gender: str = "female"
) -> str:
    """
    Create a custom avatar for an agent.

    Returns avatar_id when creation completes.
    """
    service = HeyGenEnhancedService()

    try:
        # Create avatar
        name = f"{agent_name.replace(' ', '_')}_Realtor"
        result = await service.create_custom_avatar(
            agent_id=agent_id,
            photo_url=photo_url,
            name=name,
            gender=gender
        )

        avatar_id = result["avatar_id"]

        # Wait for processing (usually 1-2 minutes)
        max_wait = 180  # 3 minutes
        start_time = datetime.now(timezone.utc)

        while True:
            elapsed = (datetime.now(timezone.utc) - start_time).seconds

            if elapsed > max_wait:
                raise TimeoutError(f"Avatar creation timeout after {max_wait}s")

            status_data = await service.check_avatar_status(avatar_id)
            status = status_data.get("status")

            if status == "completed":
                logger.info(f"Avatar {avatar_id} created successfully")
                return avatar_id

            if status == "failed":
                raise Exception(f"Avatar creation failed: {status_data.get('error')}")

            await asyncio.sleep(10)

    finally:
        await service.close()
