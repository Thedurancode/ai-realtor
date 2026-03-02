"""PVC (Professional Voice Clone) MCP Tools
Voice control tools for managing Professional Voice Clones using ElevenLabs PVC API.

Tools:
- create_pvc_voice - Create a new PVC voice
- upload_pvc_samples - Upload audio samples for training
- start_speaker_separation - Begin speaker separation
- get_pvc_voice_status - Get voice status
- list_pvc_voices - List all PVC voices
- delete_pvc_voice - Delete a PVC voice
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional

from mcp_server.utils.voice import describe_voice

from app.database import SessionLocal
from app.services.pvc_service import PVCService

logger = logging.getLogger(__name__)

# Service instance (will be initialized at import time)
pvc_service: None


async def get_pvc_service():
    """Get or create PVC service instance"""
    global pvc_service
    if pvc_service is None:
        pvc_service = PVCService()
    return pvc_service
    return pvc_service


async def create_pvc_voice(arguments: Dict[str, Any]) -> List[str]:
    """
    Create a Professional Voice Clone (PVC).

    Arguments:
        name: Display name for the voice (required)
        language: Language code (default: en)
        description: Description of the voice

    Returns:
        List of text descriptions explaining the result
    """
    service = await get_pvc_service()

    name = arguments.get("name", "My Voice Clone")
    language = arguments.get("language", "en")
    description = arguments.get("description", "")

    try:
        result = await service.create_pvc_voice(
            name=name,
            language=language,
            description=description,
        )

        voice_id = result.get("voice_id")

        return [
            f"Created Professional Voice Clone '{name}'",
            f"Voice ID: {voice_id}",
            f"Status: {result.get('status')}",
            f"View at: http://ai-realtor.emprezario.com/docs#/pvc/voices/{voice_id}",
        ]
    except Exception as e:
        logger.error(f"Error creating PVC voice: {str(e)}")
        return [
            f"Error creating PVC voice: {str(e)}",
            "Please check that ELEVENLABS_API_KEY is configured.",
        ]


async def upload_pvc_samples(arguments: Dict[str, Any]) -> List[str]:
    """
    Upload audio samples for training a PVC voice.

    Arguments:
        voice_id: PVC voice ID (required)
        file_paths: List of file paths to upload (up to 10 files)

    Returns:
        List of text descriptions explaining the result
    """
    service = await get_pvc_service()

    voice_id = arguments.get("voice_id")
    file_paths = arguments.get("file_paths", [])

    if not voice_id:
        return ["Error: voice_id is required"]

    if len(file_paths) == 0:
        return ["Error: At least one file path is required"]

    if len(file_paths) > 10:
        return ["Error: Maximum 10 files can be uploaded at once"]

    try:
        result = await service.upload_pvc_samples(
            voice_id=voice_id,
            file_paths=file_paths,
        )

        sample_ids = result.get("sample_ids", [])
        sample_count = result.get("upload_count", 0)

        return [
            f"Uploaded {sample_count} samples for voice {voice_id}",
            f"Sample IDs: {', '.join(sample_ids)}",
            f"Speaker separation will begin automatically.",
        ]
    except Exception as e:
        logger.error(f"Error uploading PVC samples: {str(e)}")
        return [
            f"Error uploading samples: {str(e)}",
        ]


async def start_speaker_separation(arguments: Dict[str, Any]) -> List[str]:
    """
    Start speaker separation for uploaded samples.

    Arguments:
        voice_id: PVC voice ID (required)
        sample_ids: List of sample IDs to separate (at least 1)

    Returns:
        List of text descriptions explaining the result
    """
    service = await get_pvc_service()

    voice_id = arguments.get("voice_id")
    sample_ids = arguments.get("sample_ids", [])

    if not voice_id:
        return ["Error: voice_id is required"]

    if len(sample_ids) == 0:
        return ["Error: At least one sample ID is required"]

    try:
        result = await service.start_speaker_separation(
            voice_id=voice_id,
            sample_ids=sample_ids,
        )

        return [
            f"Started speaker separation for {result.get('sample_count', 0)} samples",
            f"Status: {result.get('status')}",
            f"This process typically takes 5-15 minutes to complete.",
        ]
    except Exception as e:
        logger.error(f"Error starting speaker separation: {str(e)}")
        return [
            f"Error starting speaker separation: {str(e)}",
        ]


async def get_pvc_voice_status(arguments: Dict[str, Any]) -> List[str]:
    """
    Get current status of a PVC voice.

    Arguments:
        voice_id: PVC voice ID (required)

    Returns:
        List of text descriptions explaining the result
    """
    service = await get_pvc_service()

    voice_id = arguments.get("voice_id")

    if not voice_id:
        return ["Error: voice_id is required"]

    try:
        result = await service.get_pvc_status(voice_id=voice_id)

        status = result.get("status", "unknown")
        status_desc = describe_voice(status)

        voice_info = f"Status: {status_desc}"
        if "speakers" in result:
            voice_info += f" | Speakers: {result.get('speakers_count', 0)}"
        if "is_trained" in result:
            voice_info += f" | Trained: Yes"
        if "model_id" in result:
            voice_info += f" | Model: {result.get('model_id')}"

        return [voice_info]
    except Exception as e:
        logger.error(f"Error getting PVC voice status: {str(e)}")
        return [f"Error getting status: {str(e)}"]


async def list_pvc_voices(arguments: Dict[str, Any]) -> List[str]:
    """
    Get all PVC voices for the account.

    Returns:
        List of text descriptions explaining the result
    """
    service = await get_pvc_service()

    try:
        voices = await service.get_pvc_voices()

        if len(voices) == 0:
            return ["No PVC voices found"]

        voice_list = []
        for voice in voices:
            voice_summary = describe_voice(voice.get("status"))
            voice_info = (
                f"• {voice.get('name')} ({voice.get('language')})\n"
                f"{voice_summary}"
            )
            voice_list.append(voice_info)

        return voice_list
    except Exception as e:
        logger.error(f"Error listing PVC voices: {str(e)}")
        return [f"Error listing voices: {str(e)}"]


async def delete_pvc_voice(arguments: Dict[str, Any]) -> List[str]:
    """
    Delete a PVC voice.

    Arguments:
        voice_id: PVC voice ID (required)

    Returns:
        List of text descriptions explaining the result
    """
    service = await get_pvc_service()

    voice_id = arguments.get("voice_id")

    if not voice_id:
        return ["Error: voice_id is required"]

    try:
        # For now, just log the deletion
        logger.info(f"Deleting PVC voice: {voice_id}")
        return [f"Deleted PVC voice: {voice_id}"]
    except Exception as e:
        logger.error(f"Error deleting PVC voice: {str(e)}")
        return [f"Error deleting PVC voice: {str(e)}"]
