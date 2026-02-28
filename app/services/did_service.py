"""D-ID Service

Talking head video generation from static photos.
Creates lip-synced avatar videos from realtor photos.
Uses AWS Signature Version 4 authentication.
"""
import os
import json
import logging
from typing import Dict, Optional
import httpx
import asyncio
from datetime import datetime, timezone

from app.config import settings
from app.services.aws_sigv4 import create_did_signer

logger = logging.getLogger(__name__)


class DIDService:
    """
    D-ID API service for talking head video generation.

    Creates lip-synced videos from static photos with text-to-speech.
    Uses AWS Signature Version 4 for authentication.
    """

    BASE_URL = "https://api.d-id.com"
    API_VERSION = "v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DID_API_KEY")
        if not self.api_key:
            logger.warning("D-ID API key not configured - talking head videos will be disabled")
            # Create dummy signers that will fail gracefully
            self.regions = ["us-east-1"]
            self.signers = []
            self.client = httpx.AsyncClient(timeout=120.0)
            return

        # Create AWS SigV4 signers for different regions to try
        self.regions = ["us-east-1", "us-east-2", "eu-west-1", "us-west-2"]
        self.signers = [create_did_signer(self.api_key, region) for region in self.regions]

        # Base client without auth headers (added per-request)
        self.client = httpx.AsyncClient(timeout=120.0)

    async def create_talking_head(
        self,
        image_url: str,
        script: str,
        voice_id: str = "en-US-Jenny",  # Default female voice
        background_color: str = "#f8fafc"
    ) -> Dict:
        """
        Create a talking head video from a static photo.

        Args:
            image_url: URL to the person's photo
            script: Text for the person to say
            voice_id: D-ID voice ID
            background_color: Background hex color

        Returns:
            {
                "video_id": "abc123",
                "status": "processing",
                "estimated_time": 60
            }

        Raises:
            Exception: If D-ID is not configured or all regions fail
        """
        # Check if D-ID is configured
        if not self.signers:
            logger.warning("D-ID not configured, skipping talking head generation")
            raise Exception("D-ID API key not configured. Cannot generate talking head video.")

        logger.info(f"Creating D-ID talking head from {image_url}")

        # D-ID API payload format
        payload = {
            "script": {
                "type": "text",
                "input": script
            },
            "config": {
                "fluent": False,
                "pad_audio": 0.0
            },
            "source_url": image_url
        }

        # Prepare request
        url = f"{self.BASE_URL}/{self.API_VERSION}/talks"
        body = json.dumps(payload)
        base_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Try each region until one works
        last_error = None
        for i, signer in enumerate(self.signers):
            region = self.regions[i]
            try:
                # Sign request with AWS SigV4 for this region
                signed_headers = signer.sign_request("POST", url, base_headers, body)

                response = await self.client.post(
                    url,
                    headers=signed_headers,
                    content=body.encode('utf-8')
                )

                # Check if successful
                if response.status_code == 200 or response.status_code == 201:
                    result = response.json()
                    video_id = result.get("id")
                    logger.info(f"D-ID video creation started with region {region}: {video_id}")

                    # Store the successful signer for future requests
                    self.signer = signer

                    return {
                        "video_id": video_id,
                        "status": result.get("status", "processing"),
                        "estimated_time": 60
                    }
                else:
                    last_error = f"Region {region}: {response.status_code} - {response.text[:200]}"

            except Exception as e:
                last_error = f"Region {region}: {str(e)}"
                logger.warning(f"D-ID API failed with region {region}: {str(e)}")
                continue

        # All regions failed
        error_msg = f"Failed to create D-ID video after trying {len(self.regions)} regions. Last error: {last_error}"
        logger.error(error_msg)
        raise Exception(error_msg)

    async def get_video_status(self, video_id: str) -> Dict:
        """
        Check D-ID video generation status.

        Args:
            video_id: D-ID video ID

        Returns:
            {
                "id": "abc123",
                "status": "completed" | "processing" | "failed",
                "result_url": "https://...",
                "created_at": "2024-01-01T00:00:00Z",
                "error": "..."  # if failed
            }
        """
        try:
            url = f"{self.BASE_URL}/{self.API_VERSION}/talks/{video_id}"
            headers = {
                "Accept": "application/json"
            }

            # Sign request
            signed_headers = self.signer.sign_request("GET", url, headers, "")

            response = await self.client.get(
                url,
                headers=signed_headers
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Failed to check D-ID video status: {str(e)}")
            raise

    async def wait_for_video(
        self,
        video_id: str,
        timeout: int = 300,
        check_interval: int = 10
    ) -> Dict:
        """
        Wait for D-ID video to complete processing.

        Args:
            video_id: D-ID video ID to wait for
            timeout: Maximum seconds to wait (default 5 min)
            check_interval: Seconds between status checks

        Returns:
            Completed video data with result_url

        Raises:
            TimeoutError: If video doesn't complete in time
            Exception: If video generation fails
        """
        start_time = datetime.now(timezone.utc)

        while True:
            elapsed = (datetime.now(timezone.utc) - start_time).seconds

            if elapsed > timeout:
                raise TimeoutError(f"D-ID video processing timeout after {timeout}s")

            status_data = await self.get_video_status(video_id)
            status = status_data.get("status")

            logger.info(f"D-ID video {video_id} status: {status} ({elapsed}s elapsed)")

            if status == "completed":
                logger.info(f"D-ID video {video_id} completed successfully")
                return status_data

            if status == "failed":
                error_msg = status_data.get("error", "Unknown error")
                raise Exception(f"D-ID video generation failed: {error_msg}")

            await asyncio.sleep(check_interval)

    async def download_video(self, video_url: str) -> bytes:
        """
        Download video from URL.
        """
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.get(video_url)
            response.raise_for_status()
            return response.content

    async def get_available_voices(self) -> list:
        """
        List available D-ID text-to-speech voices.
        """
        try:
            response = await self.client.get(f"/{self.API_VERSION}/voices")
            response.raise_for_status()
            data = response.json()
            return data.get("voices", [])

        except Exception as e:
            logger.error(f"Failed to list D-ID voices: {str(e)}")
            # Return default voices if API fails
            return [
                {"voice_id": "en-US-Jenny", "name": "Jenny", "language": "en-US", "gender": "female"},
                {"voice_id": "en-US-James", "name": "James", "language": "en-US", "gender": "male"},
                {"voice_id": "en-US-Marcus", "name": "Marcus", "language": "en-US", "gender": "male"},
            ]

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
