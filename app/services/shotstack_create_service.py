"""Shotstack Create API Service — Generative AI Asset Factory

Consolidates text-to-speech, text-to-avatar, and text-to-image generation
into a single Shotstack API, replacing separate ElevenLabs + HeyGen calls.

Providers available via Create API:
  - shotstack   → native TTS (free with plan)
  - elevenlabs  → premium TTS with voice cloning
  - heygen      → talking-head avatar videos (24 stock avatars)
  - d-id        → alternative avatar videos
  - stability   → text-to-image generation
"""
import asyncio
import logging
import time
from typing import Dict, List, Optional, TYPE_CHECKING

import shotstack_sdk as shotstack
from shotstack_sdk.api import create_api
from shotstack_sdk.model.generated_asset import GeneratedAsset
from shotstack_sdk.model.shotstack_generated_asset import ShotstackGeneratedAsset
from shotstack_sdk.model.shotstack_generated_asset_options import ShotstackGeneratedAssetOptions
from shotstack_sdk.model.eleven_labs_generated_asset import ElevenLabsGeneratedAsset
from shotstack_sdk.model.eleven_labs_generated_asset_options import ElevenLabsGeneratedAssetOptions
from shotstack_sdk.model.hey_gen_generated_asset import HeyGenGeneratedAsset
from shotstack_sdk.model.hey_gen_generated_asset_options import HeyGenGeneratedAssetOptions
from shotstack_sdk.model.did_generated_asset import DIDGeneratedAsset
from shotstack_sdk.model.did_generated_asset_options import DIDGeneratedAssetOptions
from shotstack_sdk.model.stability_ai_generated_asset import StabilityAiGeneratedAsset
from shotstack_sdk.model.stability_ai_generated_asset_options import StabilityAiGeneratedAssetOptions

from app.config import settings

logger = logging.getLogger(__name__)

# Polling settings
POLL_INTERVAL = 5  # seconds
DEFAULT_TIMEOUT = 600  # 10 minutes

# Stock avatar IDs available in HeyGen via Shotstack Create API
HEYGEN_STOCK_AVATARS = [
    "anna_commercial", "josh_lite", "susan_casual", "tyler_office",
    "monica_presenter", "kayla_casual", "mark_professional",
]

# Shotstack native TTS voices
SHOTSTACK_VOICES = [
    "matthew", "joanna", "ivy", "justin", "kendra", "kimberly",
    "salli", "joey", "ruth", "stephen", "brian", "amy", "emma",
]

# Stability AI style presets
STABILITY_STYLES = [
    "photographic", "cinematic", "digital-art", "fantasy-art",
    "analog-film", "neon-punk", "isometric", "origami",
    "3d-model", "pixel-art", "enhance", "comic-book",
]


class ShotstackCreateService:
    """Shotstack Create API client — unified generative AI asset factory."""

    def __init__(self, api_key: Optional[str] = None, stage: Optional[bool] = None):
        self.api_key = api_key or settings.shotstack_api_key
        self.stage = stage if stage is not None else settings.shotstack_stage

        host = (
            "https://api.shotstack.io/create/stage"
            if self.stage
            else "https://api.shotstack.io/create/v1"
        )

        config = shotstack.Configuration(host=host)
        config.api_key["DeveloperKey"] = self.api_key

        self._api_client = shotstack.ApiClient(config)
        self._api = create_api.CreateApi(self._api_client)

    # ------------------------------------------------------------------
    # Core: submit + poll
    # ------------------------------------------------------------------

    def submit_asset(self, asset: GeneratedAsset) -> str:
        """Submit a generated asset request. Returns the asset ID."""
        try:
            response = self._api.post_generate_asset(asset)
        except Exception as e:
            body = getattr(e, "body", None)
            if body:
                import json as _json
                try:
                    parsed = _json.loads(body) if isinstance(body, str) else body
                    msg = parsed.get("data", {}).get("message") or parsed.get("message", str(e))
                    raise RuntimeError(f"Shotstack Create API error: {msg}") from e
                except (ValueError, AttributeError):
                    pass
            raise
        data = response.get("data", {})
        asset_id = data.get("id")
        logger.info(f"Create API asset submitted: {asset_id}")
        return asset_id

    def get_asset_status(self, asset_id: str) -> Dict:
        """Get the status of a generated asset.

        Returns: {"id", "status", "url", "provider", "type"}
        """
        response = self._api.get_generated_asset(asset_id)
        data = response.get("data", {})
        attrs = data.get("attributes", {})
        return {
            "id": data.get("id"),
            "status": attrs.get("status"),
            "url": attrs.get("url"),
            "provider": attrs.get("provider"),
            "type": attrs.get("type"),
        }

    def poll_until_ready(self, asset_id: str, timeout: int = DEFAULT_TIMEOUT) -> Dict:
        """Synchronously poll until asset is done or failed."""
        start = time.time()
        while time.time() - start < timeout:
            result = self.get_asset_status(asset_id)
            status = result.get("status")
            if status == "done":
                logger.info(f"Asset {asset_id} ready: {result.get('url')}")
                return result
            if status == "failed":
                raise RuntimeError(f"Asset generation failed: {asset_id}")
            time.sleep(POLL_INTERVAL)
        raise TimeoutError(f"Asset {asset_id} timed out after {timeout}s")

    async def poll_until_ready_async(self, asset_id: str, timeout: int = DEFAULT_TIMEOUT) -> Dict:
        """Async version of poll_until_ready."""
        start = time.time()
        while time.time() - start < timeout:
            result = self.get_asset_status(asset_id)
            status = result.get("status")
            if status == "done":
                logger.info(f"Asset {asset_id} ready: {result.get('url')}")
                return result
            if status == "failed":
                raise RuntimeError(f"Asset generation failed: {asset_id}")
            await asyncio.sleep(POLL_INTERVAL)
        raise TimeoutError(f"Asset {asset_id} timed out after {timeout}s")

    # ------------------------------------------------------------------
    # Text-to-Speech (Shotstack native — no extra API key)
    # ------------------------------------------------------------------

    def create_tts_shotstack(
        self,
        text: str,
        voice: str = "matthew",
        language: str = "en",
        newscaster: bool = False,
    ) -> str:
        """Generate TTS audio using Shotstack's native engine.

        Free with Shotstack plan. No ElevenLabs key needed.
        Returns asset ID (poll for URL).
        """
        options = ShotstackGeneratedAssetOptions(
            type="text-to-speech",
            text=text,
            voice=voice,
            language=language,
            newscaster=newscaster,
        )
        asset = ShotstackGeneratedAsset(provider="shotstack", options=options)
        return self.submit_asset(asset)

    # ------------------------------------------------------------------
    # Text-to-Speech (ElevenLabs via Shotstack — uses your EL key)
    # ------------------------------------------------------------------

    def create_tts_elevenlabs(
        self,
        text: str,
        voice: str = "Rachel",
    ) -> str:
        """Generate TTS audio using ElevenLabs through Shotstack Create API.

        Supports ElevenLabs voice IDs or names. Your ElevenLabs key must be
        registered with Shotstack (dashboard → integrations).
        Returns asset ID.
        """
        options = ElevenLabsGeneratedAssetOptions(
            type="text-to-speech",
            text=text,
            voice=voice,
        )
        asset = ElevenLabsGeneratedAsset(provider="elevenlabs", options=options)
        return self.submit_asset(asset)

    # ------------------------------------------------------------------
    # Text-to-Avatar (HeyGen via Shotstack)
    # ------------------------------------------------------------------

    def create_avatar_heygen(
        self,
        text: str,
        avatar: str = "anna_commercial",
        voice: Optional[str] = None,
        avatar_style: str = "normal",
        background: str = "#FFFFFF",
        ratio: str = "16:9",
        test: bool = False,
    ) -> str:
        """Generate a talking-head video using HeyGen through Shotstack.

        24 stock avatars available. Audio generated server-side — no separate
        TTS call needed. The avatar lip-syncs to the generated speech.
        Returns asset ID.
        """
        kwargs = {
            "type": "text-to-avatar",
            "text": text,
            "avatar": avatar,
            "avatar_style": avatar_style,
            "background": background,
            "ratio": ratio,
            "test": test,
        }
        if voice:
            kwargs["voice"] = voice
        options = HeyGenGeneratedAssetOptions(**kwargs)
        asset = HeyGenGeneratedAsset(provider="heygen", options=options)
        return self.submit_asset(asset)

    # ------------------------------------------------------------------
    # Text-to-Avatar (D-ID via Shotstack)
    # ------------------------------------------------------------------

    def create_avatar_did(
        self,
        text: str,
        avatar: str = "amy",
        background: str = "#FFFFFF",
    ) -> str:
        """Generate a talking-head video using D-ID through Shotstack.
        Returns asset ID.
        """
        options = DIDGeneratedAssetOptions(
            type="text-to-avatar",
            text=text,
            avatar=avatar,
            background=background,
        )
        asset = DIDGeneratedAsset(provider="d-id", options=options)
        return self.submit_asset(asset)

    # ------------------------------------------------------------------
    # Text-to-Image (Stability AI via Shotstack)
    # ------------------------------------------------------------------

    def create_image_stability(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 576,
        engine: str = "stable-diffusion-xl-1024-v1-0",
        steps: int = 30,
        cfg_scale: float = 7.0,
        style_preset: str = "photographic",
        seed: Optional[int] = None,
    ) -> str:
        """Generate an image using Stability AI through Shotstack.

        Great for property lifestyle scenes, marketing backgrounds, etc.
        Returns asset ID.
        """
        kwargs = {
            "type": "text-to-image",
            "prompt": prompt,
            "width": width,
            "height": height,
            "engine": engine,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "style_preset": style_preset,
        }
        if seed is not None:
            kwargs["seed"] = seed
        options = StabilityAiGeneratedAssetOptions(**kwargs)
        asset = StabilityAiGeneratedAsset(provider="stability-ai", options=options)
        return self.submit_asset(asset)

    # ------------------------------------------------------------------
    # Text-to-Image (Shotstack native)
    # ------------------------------------------------------------------

    def create_image_shotstack(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 576,
    ) -> str:
        """Generate an image using Shotstack's native engine.
        Returns asset ID.
        """
        options = ShotstackGeneratedAssetOptions(
            type="text-to-image",
            prompt=prompt,
            width=width,
            height=height,
        )
        asset = ShotstackGeneratedAsset(provider="shotstack", options=options)
        return self.submit_asset(asset)

    # ------------------------------------------------------------------
    # Consolidated pipeline helpers
    # ------------------------------------------------------------------

    async def generate_tts(
        self,
        text: str,
        voice: str = "matthew",
        provider: str = "shotstack",
        timeout: int = DEFAULT_TIMEOUT,
    ) -> str:
        """Generate TTS and wait for the URL. Returns the hosted audio URL."""
        if provider == "elevenlabs":
            asset_id = self.create_tts_elevenlabs(text=text, voice=voice)
        else:
            asset_id = self.create_tts_shotstack(text=text, voice=voice)
        result = await self.poll_until_ready_async(asset_id, timeout=timeout)
        return result["url"]

    async def generate_avatar(
        self,
        text: str,
        avatar: str = "anna_commercial",
        voice: Optional[str] = None,
        provider: str = "heygen",
        background: str = "#00FF00",
        ratio: str = "16:9",
        timeout: int = DEFAULT_TIMEOUT,
    ) -> str:
        """Generate a talking-head avatar and wait for the URL."""
        if provider == "d-id":
            asset_id = self.create_avatar_did(text=text, avatar=avatar, background=background)
        else:
            asset_id = self.create_avatar_heygen(
                text=text, avatar=avatar, voice=voice,
                background=background, ratio=ratio,
            )
        result = await self.poll_until_ready_async(asset_id, timeout=timeout)
        return result["url"]

    async def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 576,
        provider: str = "stability-ai",
        style_preset: str = "photographic",
        timeout: int = DEFAULT_TIMEOUT,
    ) -> str:
        """Generate an image and wait for the URL."""
        if provider == "shotstack":
            asset_id = self.create_image_shotstack(prompt=prompt, width=width, height=height)
        else:
            asset_id = self.create_image_stability(
                prompt=prompt, width=width, height=height, style_preset=style_preset,
            )
        result = await self.poll_until_ready_async(asset_id, timeout=timeout)
        return result["url"]

    def close(self):
        self._api_client.close()

    async def aclose(self):
        self._api_client.close()


_shotstack_create_service: Optional["ShotstackCreateService"] = None


def get_shotstack_create_service() -> "ShotstackCreateService":
    global _shotstack_create_service
    if _shotstack_create_service is None:
        _shotstack_create_service = ShotstackCreateService()
    return _shotstack_create_service
