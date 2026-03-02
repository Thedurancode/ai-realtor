"""PVC (Professional Voice Clone) Service
Handles high-quality voice cloning using ElevenLabs PVC API.

Features:
- Create PVC voices with recording upload
- Upload audio samples for training
- Manage speaker separation
- Fine-tune voice models
- Track PVC status and training progress
- Retrieve completed voice IDs
- Link PVCs to agents/properties

Uses AWS Signature Version 4 authentication.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

from app.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.elevenlabs.io"
API_VERSION = "v1"


class PVCService:
    """
    Professional Voice Clone service for creating high-quality voice clones.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            logger.warning("ElevenLabs API key not configured - PVC will be disabled")
            # Create dummy values that will fail gracefully
            self.client = httpx.AsyncClient(timeout=300.0)
        else:
            # Base client without auth headers (added per-request)
            self.client = httpx.AsyncClient(timeout=300.0)

    async def create_pvc_voice(
        self,
        name: str,
        language: str = "en",
        description: str,
    ) -> Dict[str, Any]:
        """
        Create a new PVC voice (Instant Voice Clone equivalent).

        Args:
            name: Display name for the voice
            language: Language code (default: en)
            description: Description of the voice

        Returns:
            {
                "voice_id": "abc123",
                "status": "created",
                "description": "Creating voice...",
            }
        """
        if not self.api_key:
            raise Exception("ElevenLabs API key not configured. Cannot create PVC voice.")

        logger.info(f"Creating PVC voice: {name}")

        url = f"{BASE_URL}/{API_VERSION}/voices"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        payload = {
            "name": name,
            "language": language,
            "description": description,
            "instant_clone": True,  # Mark as PVC (not instant clone)
        }

        try:
            response = await self.client.post(url, headers=headers, json=payload)
            response.raise_for_status()

            result = response.json()
            voice_id = result.get("id")
            logger.info(f"PVC voice created with ID: {voice_id}")

            return {
                "voice_id": voice_id,
                "name": name,
                "language": language,
                "description": description,
                "status": result.get("status", "processing"),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error creating PVC voice: {e}")
            raise Exception(f"Failed to create PVC voice: {str(e)}")
        except Exception as e:
            logger.error(f"Error creating PVC voice: {str(e)}")
            raise Exception(f"Failed to create PVC voice: {str(e)}")

    async def upload_pvc_samples(
        self,
        voice_id: str,
        file_paths: List[str],
    ) -> Dict[str, Any]:
        """
        Upload audio samples for training a PVC voice.

        Args:
            voice_id: PVC voice ID from create_pvc_voice
            file_paths: List of file paths to upload

        Returns:
            {
                "voice_id": voice_id,
                "sample_ids": ["sample1", "sample2"],
                "upload_count": 2,
            }
        """
        if not self.api_key:
            raise Exception("ElevenLabs API key not configured. Cannot upload PVC samples.")

        logger.info(f"Uploading {len(file_paths)} samples for voice {voice_id}")

        url = f"{BASE_URL}/{API_VERSION}/voices/{voice_id}/samples"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "multipart/form-data",
            "Accept": "application/json"
        }

        # Build multipart form with files
        files = [("files", open(filepath, "rb")) for filepath in file_paths]

        try:
            response = await self.client.post(url, headers=headers, files=files)
            response.raise_for_status()

            result = response.json()
            sample_ids = result.get("sample_ids", [])

            logger.info(f"Uploaded {len(sample_ids)} samples for voice {voice_id}")

            return {
                "voice_id": voice_id,
                "sample_ids": sample_ids,
                "upload_count": len(sample_ids),
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error uploading PVC samples: {e}")
            raise Exception(f"Failed to upload PVC samples: {str(e)}")
        except Exception as e:
            logger.error(f"Error uploading PVC samples: {str(e)}")
            raise Exception(f"Failed to upload PVC samples: {str(e)}")

    async def start_speaker_separation(
        self,
        voice_id: str,
        sample_ids: List[str],
    ) -> Dict[str, Any]:
        """
        Begin speaker separation for uploaded samples.

        Args:
            voice_id: PVC voice ID
            sample_ids: List of sample IDs to separate

        Returns:
            {
                "voice_id": voice_id,
                "status": "separating",
                "sample_count": len(sample_ids),
            }
        """
        if not self.api_key:
            raise Exception("ElevenLabs API key not configured. Cannot start speaker separation.")

        logger.info(f"Starting speaker separation for {len(sample_ids)} samples")

        url = f"{BASE_URL}/{API_VERSION}/voices/{voice_id}/samples/speakers"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        payload = {
            "sample_ids": sample_ids
        }

        try:
            response = await self.client.post(url, headers=headers, json=payload)
            response.raise_for_status()

            result = response.json()
            logger.info(f"Speaker separation started for voice {voice_id}")

            return {
                "voice_id": voice_id,
                "status": result.get("status", "separating"),
                "sample_count": len(sample_ids),
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error starting speaker separation: {e}")
            raise Exception(f"Failed to start speaker separation: {str(e)}")
        except Exception as e:
            logger.error(f"Error starting speaker separation: {str(e)}")
            raise Exception(f"Failed to start speaker separation: {str(e)}")

    async def get_pvc_status(
        self,
        voice_id: str,
    ) -> Dict[str, Any]:
        """
        Get current status of a PVC voice.

        Args:
            voice_id: PVC voice ID

        Returns:
            Full voice details with status
        """
        if not self.api_key:
            raise Exception("ElevenLabs API key not configured. Cannot get PVC status.")

        url = f"{BASE_URL}/{API_VERSION}/voices/{voice_id}"
        headers = {
            "xi-api-key": self.api_key,
            "Accept": "application/json"
        }

        try:
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()

            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting PVC status: {e}")
            raise Exception(f"Failed to get PVC status: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting PVC status: {str(e)}")
            raise Exception(f"Failed to get PVC status: {str(e)}")

    async def get_pvc_voices(self) -> List[Dict[str, Any]]:
        """
        Get all PVC voices for the account.

        Returns:
            List of voice objects with IDs, names, languages, etc.
        """
        if not self.api_key:
            logger.warning("ElevenLabs API key not configured - returning empty list")
            return []

        url = f"{BASE_URL}/{API_VERSION}/voices"
        headers = {
            "xi-api-key": self.api_key,
            "Accept": "application/json"
        }

        try:
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()
            voices = data.get("voices", [])

            logger.info(f"Retrieved {len(voices)} PVC voices")

            return voices
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error listing PVC voices: {e}")
            raise Exception(f"Failed to list PVC voices: {str(e)}")
        except Exception as e:
            logger.error(f"Error listing PVC voices: {str(e)}")
            raise Exception(f"Failed to list PVC voices: {str(e)}")

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
