"""PixVerse Service (via Replicate API)

Image-to-video generation for property footage.
Converts static property photos into dynamic video clips.
"""
import logging
from typing import List, Dict
from datetime import datetime, timezone
import httpx
import asyncio

from app.config import settings

logger = logging.getLogger(__name__)


class PixVerseService:
    """
    PixVerse image-to-video generation via Replicate API.

    Generates video clips from property photos with camera movements.
    """

    REPLICATE_API_URL = "https://api.replicate.com/v1"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.replicate_api_key
        if not self.api_key:
            logger.warning("Replicate API key not configured")

        self.client = httpx.AsyncClient(
            base_url=self.REPLICATE_API_URL,
            headers={
                "Authorization": f"Token {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=300.0  # 5 minute timeout
        )

    async def generate_video_clip(
        self,
        photo_url: str,
        prompt: str,
        duration: int = 8,
        resolution: str = "1080p",
        camera_movement: str = "pan_right",
        motion_bucket_id: int = 127
    ) -> Dict:
        """
        Generate video clip from property photo using PixVerse.

        Args:
            photo_url: URL of property photo
            prompt: Description of desired video (e.g., "Luxury property walkthrough")
            duration: Video duration in seconds (4-12 recommended)
            resolution: "720p", "1080p", or "4k"
            camera_movement: "pan_left", "pan_right", "zoom_in", "zoom_out", "static"
            motion_bucket_id: Motion intensity (1-255, higher = more motion)

        Returns:
            {
                "clip_id": "replicate_abc123",
                "video_url": "https://...",
                "duration": 8.0,
                "status": "succeeded"
            }

        Raises:
            Exception: If generation fails
        """
        logger.info(f"Generating PixVerse clip from {photo_url}")

        # PixVerse v4 model via Replicate
        model_version = "lucataco/pixverse-v4"

        payload = {
            "input": {
                "image": photo_url,
                "prompt": prompt,
                "duration": duration,
                "resolution": resolution,
                "camera_movement": camera_movement,
                "motion_bucket_id": motion_bucket_id
            }
        }

        try:
            # Create prediction
            response = await self.client.post("/predictions", json=payload)
            response.raise_for_status()

            prediction = response.json()
            prediction_id = prediction["id"]
            status_url = prediction["urls"]["get"]

            logger.info(f"Prediction created: {prediction_id}")

            # Poll for completion
            return await self._wait_for_prediction(prediction_id)

        except httpx.HTTPStatusError as e:
            logger.error(f"Replicate API error: {e.response.text}")
            raise Exception(f"Failed to generate video clip: {e.response.text}")
        except Exception as e:
            logger.error(f"Video clip generation error: {str(e)}")
            raise

    async def _wait_for_prediction(
        self,
        prediction_id: str,
        timeout: int = 600,
        check_interval: int = 10
    ) -> Dict:
        """
        Wait for Replicate prediction to complete.

        Args:
            prediction_id: Replicate prediction ID
            timeout: Maximum seconds to wait (10 min default)
            check_interval: Seconds between checks

        Returns:
            Prediction result with video URL

        Raises:
            TimeoutError: If prediction doesn't complete
            Exception: If prediction fails
        """
        start_time = datetime.now(timezone.utc)

        while True:
            elapsed = (datetime.now(timezone.utc) - start_time).seconds

            if elapsed > timeout:
                raise TimeoutError(f"Prediction timeout after {timeout}s")

            # Check status
            response = await self.client.get(f"/predictions/{prediction_id}")
            response.raise_for_status()

            prediction = response.json()
            status = prediction.get("status")

            logger.info(f"Prediction {prediction_id}: {status} ({elapsed}s)")

            if status == "succeeded":
                output = prediction.get("output")
                # PixVerse returns video URL as output
                video_url = output if isinstance(output, str) else output.get("video_url")

                return {
                    "clip_id": prediction_id,
                    "video_url": video_url,
                    "duration": prediction.get("metrics", {}).get("duration", 8.0),
                    "status": "succeeded"
                }

            if status == "failed":
                error = prediction.get("error", "Unknown error")
                raise Exception(f"Prediction failed: {error}")

            if status == "canceled":
                raise Exception("Prediction was canceled")

            await asyncio.sleep(check_interval)

    async def batch_generate_clips(
        self,
        photo_urls: List[str],
        prompt: str,
        concurrent: int = 3,
        **kwargs
    ) -> List[Dict]:
        """
        Generate multiple video clips concurrently.

        Args:
            photo_urls: List of photo URLs
            prompt: Prompt for all clips
            concurrent: Max concurrent generations (to avoid rate limits)
            **kwargs: Additional arguments for generate_video_clip

        Returns:
            List of clip results (same order as input)
        """
        logger.info(f"Batch generating {len(photo_urls)} clips with concurrency={concurrent}")

        results = [None] * len(photo_urls)

        # Process in batches
        for i in range(0, len(photo_urls), concurrent):
            batch = photo_urls[i:i + concurrent]
            batch_indices = list(range(i, min(i + concurrent, len(photo_urls))))

            # Generate clips concurrently
            tasks = [
                self.generate_video_clip(url, prompt, **kwargs)
                for url in batch
            ]

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Store results
            for idx, result in zip(batch_indices, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Clip {idx} failed: {str(result)}")
                    results[idx] = {
                        "error": str(result),
                        "status": "failed"
                    }
                else:
                    results[idx] = result

            logger.info(f"Batch {i//concurrent + 1} completed")

        successful = sum(1 for r in results if r and r.get("status") == "succeeded")
        logger.info(f"Batch generation complete: {successful}/{len(photo_urls)} successful")

        return results

    async def get_property_footage_prompts(
        self,
        property_data: Dict,
        style: str = "luxury"
    ) -> str:
        """
        Generate optimized prompt for property footage.

        Args:
            property_data: Property details
            style: Video style (luxury, friendly, professional)

        Returns:
            Optimized prompt for PixVerse
        """
        base_prompts = {
            "luxury": "Cinematic luxury property walkthrough, slow pan, elegant lighting, high-end real estate",
            "friendly": "Warm and inviting home tour, natural lighting, cozy atmosphere, family home",
            "professional": "Professional property presentation, steady camera, clean angles, business real estate"
        }

        base = base_prompts.get(style, base_prompts["luxury"])

        # Add property-specific details
        details = []
        if property_data.get("property_type"):
            details.append(property_data["property_type"])
        if property_data.get("bedrooms"):
            details.append(f"{property_data['bedrooms']} bedroom")

        if details:
            return f"{base}, {', '.join(details)}"
        return base

    async def estimate_cost(self, num_clips: int) -> float:
        """
        Estimate cost for video clip generation.

        PixVerse via Replicate: ~$0.01-0.05 per clip

        Args:
            num_clips: Number of clips to generate

        Returns:
            Estimated cost in USD
        """
        # Replicate pricing varies; estimate based on typical PixVerse costs
        cost_per_clip = 0.02  # Conservative estimate
        return num_clips * cost_per_clip

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# ============================================================================
# Helper Functions
# ============================================================================

async def generate_property_footage(
    photo_urls: List[str],
    property_data: Dict,
    style: str = "luxury",
    max_clips: int = 5,
    concurrent: int = 3
) -> List[Dict]:
    """
    Generate property footage clips from photos.

    Args:
        photo_urls: Property photo URLs
        property_data: Property details for prompt generation
        style: Video style
        max_clips: Maximum clips to generate
        concurrent: Concurrent generations

    Returns:
        List of successful clip results with video URLs
    """
    service = PixVerseService()

    try:
        # Generate prompt
        prompt = await service.get_property_footage_prompts(property_data, style)

        # Limit clips
        photos_to_use = photo_urls[:max_clips]

        # Generate clips
        results = await service.batch_generate_clips(
            photo_urls=photos_to_use,
            prompt=prompt,
            duration=8,
            resolution="1080p",
            camera_movement="pan_right",
            concurrent=concurrent
        )

        # Filter successful results
        successful_clips = [r for r in results if r.get("status") == "succeeded"]

        logger.info(f"Generated {len(successful_clips)}/{len(photos_to_use)} footage clips")

        return successful_clips

    finally:
        await service.close()
