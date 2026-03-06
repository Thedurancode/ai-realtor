"""HeyGen Enhanced Service

Photo Avatar creation and talking head video generation via HeyGen API v2.

Flow:
1. Upload headshot image → upload.heygen.com/v1/asset → image_key
2. Create photo avatar group → /v2/photo_avatar/avatar_group/create → group_id
3. List avatars in group → /v2/photo_avatar/avatar_group/{group_id} → talking_photo_id
4. Generate video → /v1/video/create_avatar_video → video_id
5. Poll status → /v1/video_status.get → video_url
"""
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, timezone
import httpx
import asyncio

from app.config import settings

logger = logging.getLogger(__name__)


class HeyGenEnhancedService:
    """HeyGen service for photo avatar creation and talking head video generation."""

    BASE_URL = "https://api.heygen.com"
    UPLOAD_URL = "https://upload.heygen.com"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.heygen_api_key
        if not self.api_key:
            logger.warning("HeyGen API key not configured")

        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
            },
            timeout=120.0,
        )

    # ------------------------------------------------------------------
    # Avatar creation (photo avatar)
    # ------------------------------------------------------------------

    async def upload_image_asset(self, image_path: str) -> str:
        """
        Upload a local image file to HeyGen's asset storage.

        Args:
            image_path: Local path to the image file.

        Returns:
            image_key (e.g. "image/<uuid>/original.png")
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Determine content type from extension
        ext = path.suffix.lower()
        content_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
        }
        content_type = content_types.get(ext, "image/png")

        async with httpx.AsyncClient(timeout=60.0) as upload_client:
            resp = await upload_client.post(
                f"{self.UPLOAD_URL}/v1/asset",
                headers={
                    "x-api-key": self.api_key,
                    "Content-Type": content_type,
                },
                content=path.read_bytes(),
            )
            resp.raise_for_status()
            data = resp.json()

        image_key = data.get("data", {}).get("image_key")
        if not image_key:
            raise RuntimeError(f"Upload returned no image_key: {data}")

        logger.info(f"Uploaded image asset: {image_key}")
        return image_key

    async def create_photo_avatar_group(self, name: str, image_key: str) -> Dict:
        """
        Create a photo avatar group from an uploaded image.

        Args:
            name: Display name for the avatar.
            image_key: Key returned from upload_image_asset.

        Returns:
            {"group_id": "...", "status": "pending", ...}
        """
        resp = await self.client.post(
            "/v2/photo_avatar/avatar_group/create",
            json={"name": name, "image_key": image_key},
        )
        resp.raise_for_status()
        result = resp.json()

        data = result.get("data", {})
        group_id = data.get("group_id") or data.get("id")
        status = data.get("status", "pending")

        logger.info(f"Created photo avatar group: {group_id} (status={status})")
        return {"group_id": group_id, "status": status, "data": data}

    async def create_custom_avatar(
        self,
        agent_id: int,
        photo_path: str,
        name: str,
    ) -> Dict:
        """
        Upload image → create photo avatar group → return talking_photo_id.

        The group_id returned by create_photo_avatar_group IS the talking_photo_id.
        No polling needed — the avatar is available immediately.

        Args:
            agent_id: Agent ID for logging.
            photo_path: Local file path to the headshot image.
            name: Avatar display name.

        Returns:
            {"avatar_id": "<talking_photo_id>"}
        """
        logger.info(f"Creating photo avatar for agent {agent_id} from {photo_path}")

        # Step 1: Upload image
        image_key = await self.upload_image_asset(photo_path)

        # Step 2: Create avatar group — the group_id IS the talking_photo_id
        result = await self.create_photo_avatar_group(name=name, image_key=image_key)
        talking_photo_id = result["group_id"]

        logger.info(f"Photo avatar created: talking_photo_id={talking_photo_id}")
        return {"avatar_id": talking_photo_id}

    async def verify_talking_photo(self, talking_photo_id: str) -> bool:
        """Verify a talking photo exists in the account's avatar list."""
        resp = await self.client.get("/v2/avatars")
        resp.raise_for_status()
        photos = resp.json().get("data", {}).get("talking_photos", [])
        return any(p.get("talking_photo_id") == talking_photo_id for p in photos)

    # ------------------------------------------------------------------
    # Audio asset upload
    # ------------------------------------------------------------------

    async def upload_audio_asset(self, audio_path: str) -> str:
        """
        Upload a local audio file to HeyGen's asset storage.

        Args:
            audio_path: Local path to the audio file (.mp3, .wav, .m4a).

        Returns:
            audio_asset_id (UUID string)
        """
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio not found: {audio_path}")

        ext = path.suffix.lower()
        content_types = {
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".m4a": "audio/mp4",
            ".ogg": "audio/ogg",
            ".flac": "audio/flac",
        }
        content_type = content_types.get(ext, "audio/mpeg")

        async with httpx.AsyncClient(timeout=60.0) as upload_client:
            resp = await upload_client.post(
                f"{self.UPLOAD_URL}/v1/asset",
                headers={
                    "x-api-key": self.api_key,
                    "Content-Type": content_type,
                },
                content=path.read_bytes(),
            )
            resp.raise_for_status()
            data = resp.json()

        asset_id = data.get("data", {}).get("id")
        if not asset_id:
            raise RuntimeError(f"Upload returned no asset id: {data}")

        logger.info(f"Uploaded audio asset: {asset_id}")
        return asset_id

    # ------------------------------------------------------------------
    # Video generation
    # ------------------------------------------------------------------

    async def generate_talking_head(
        self,
        avatar_id: str,
        script: str,
        voice_id: Optional[str] = None,
        audio_asset_id: Optional[str] = None,
        background_color: str = "#f8fafc",
    ) -> Dict:
        """
        Generate a talking head video using a photo avatar.

        Supports two voice modes:
        - **Audio mode** (preferred): pass audio_asset_id from a pre-generated
          ElevenLabs TTS file uploaded to HeyGen.
        - **TTS mode** (fallback): pass voice_id for HeyGen's built-in TTS.

        Args:
            avatar_id: The talking_photo_id.
            script: Text for the avatar to speak (used for TTS mode).
            voice_id: HeyGen voice ID (TTS mode).
            audio_asset_id: HeyGen audio asset ID (audio mode, takes priority).
            background_color: Background hex color.

        Returns:
            {"video_id": "...", "status": "processing"}
        """
        logger.info(f"Generating talking head video with avatar {avatar_id}")

        # Build voice config — audio mode takes priority
        if audio_asset_id:
            voice_config = {
                "type": "audio",
                "audio_asset_id": audio_asset_id,
            }
            logger.info(f"Using audio asset: {audio_asset_id}")
        else:
            voice_config = {
                "type": "text",
                "input_text": script,
            }
            if voice_id:
                voice_config["voice_id"] = voice_id

        payload = {
            "video_inputs": [
                {
                    "character": {
                        "type": "talking_photo",
                        "talking_photo_id": avatar_id,
                    },
                    "voice": voice_config,
                    "background": {
                        "type": "color",
                        "value": background_color,
                    },
                }
            ],
            "dimension": {"width": 1920, "height": 1080},
        }

        try:
            resp = await self.client.post("/v2/video/generate", json=payload)
            resp.raise_for_status()
            result = resp.json()

            video_id = result.get("data", {}).get("video_id")
            logger.info(f"Video generation started: {video_id}")

            return {
                "video_id": video_id,
                "status": "processing",
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"HeyGen video generate error: {e.response.text}")
            raise RuntimeError(f"Video generation failed: {e.response.text}")

    async def get_video_status(self, video_id: str) -> Dict:
        """Check video generation status."""
        try:
            resp = await self.client.get(
                "/v1/video_status.get",
                params={"video_id": video_id},
            )
            resp.raise_for_status()
            return resp.json().get("data", {})
        except Exception as e:
            logger.error(f"Failed to check video status: {e}")
            raise

    async def wait_for_video(
        self,
        video_id: str,
        timeout: int = 600,
        check_interval: int = 10,
    ) -> Dict:
        """
        Poll until video is complete.

        Returns:
            Video data dict with video_url when done.
        """
        start = datetime.now(timezone.utc)
        while True:
            elapsed = (datetime.now(timezone.utc) - start).total_seconds()
            if elapsed > timeout:
                raise TimeoutError(f"Video processing timeout after {timeout}s")

            status_data = await self.get_video_status(video_id)
            status = status_data.get("status")
            logger.info(f"Video {video_id}: {status} ({int(elapsed)}s)")

            if status == "completed":
                return status_data

            if status == "failed":
                error_msg = status_data.get("error", "Unknown error")
                raise RuntimeError(f"Video generation failed: {error_msg}")

            await asyncio.sleep(check_interval)

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
