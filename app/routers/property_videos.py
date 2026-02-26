"""Property Video Generation API with ElevenLabs Voiceover"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field

from app.database import SessionLocal
from app.services.property_video_service import PropertyVideoService


router = APIRouter(prefix="/v1/property-videos", tags=["property-videos"])


class GenerateVideoRequest(BaseModel):
    """Request to generate property video."""
    property_id: int = Field(..., description="Property ID to generate video for")
    agent_id: int = Field(..., description="Agent ID for branding")
    voice_id: Optional[str] = Field(
        default="21m00Tcm4TlvDq8ikWAM",
        description="ElevenLabs voice ID (default: male voice)"
    )
    output_dir: Optional[str] = Field(
        default=None,
        description="Output directory (default: temp dir)"
    )


class GenerateVideoResponse(BaseModel):
    """Response from video generation."""
    video_path: str
    audio_path: str
    script: str
    duration_seconds: float
    property_id: int
    photos_used: int
    brand: dict


def get_db():
    """Dependency to get DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/generate", response_model=GenerateVideoResponse, status_code=status.HTTP_201_CREATED)
async def generate_property_video(
    request: GenerateVideoRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a property showcase video with AI voiceover.

    Video includes:
    - Company logo intro (3 seconds)
    - Property photo slideshow (4 seconds per photo)
    - Property details overlay (price, address, beds, baths, sqft)
    - ElevenLabs AI voiceover with property description

    **Parameters:**
    - **property_id**: ID of the property to feature
    - **agent_id**: ID of the agent (for branding/logo)
    - **voice_id**: Optional ElevenLabs voice ID for voiceover
    - **output_dir**: Optional custom output directory

    **Example Request:**
    ```json
    {
      "property_id": 3,
      "agent_id": 5,
      "voice_id": "21m00Tcm4TlvDq8ikWAM"
    }
    ```

    **Returns:**
    - Video file path
    - Audio file path
    - Generated script text
    - Video duration
    - Number of photos used
    """
    try:
        service = PropertyVideoService()

        result = await service.generate_property_video(
            db=db,
            property_id=request.property_id,
            agent_id=request.agent_id,
            output_path=request.output_dir,
            voice_id=request.voice_id
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate video: {str(e)}"
        )


@router.get("/voices")
async def list_available_voices():
    """
    Get list of available ElevenLabs voices for voiceover.

    Returns a list of all available voices with their IDs, names, and categories.

    **Example Response:**
    ```json
    {
      "voices": [
        {
          "voice_id": "21m00Tcm4TlvDq8ikWAM",
          "name": "Rachel",
          "category": "cloned"
        }
      ]
    }
    ```
    """
    try:
        service = PropertyVideoService()
        voices = service.get_available_voices()
        return {"voices": voices}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch voices: {str(e)}"
        )


@router.post("/script-preview")
async def generate_script_preview(
    property_id: int,
    db: Session = Depends(get_db)
):
    """
    Generate a preview of the voiceover script without creating the video.

    Useful for reviewing the script before generating the full video.

    **Parameters:**
    - **property_id**: ID of the property

    **Returns:**
    - Generated script text
    - Estimated duration
    - Photo count
    """
    from app.models.property import Property
    from app.models.zillow_enrichment import ZillowEnrichment

    property = db.query(Property).filter_by(id=property_id).first()
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property {property_id} not found"
        )

    enrichment = db.query(ZillowEnrichment).filter_by(property_id=property_id).first()

    service = PropertyVideoService()
    script = service._generate_script(property, enrichment)

    # Get photo count
    photo_count = 0
    if enrichment and enrichment.photos:
        import json
        photos = json.loads(enrichment.photos) if isinstance(enrichment.photos, str) else enrichment.photos
        photo_count = len(photos)

    # Estimate duration (rough estimate: 150 words per minute)
    word_count = len(script.split())
    estimated_duration = word_count / 150 * 60  # seconds

    return {
        "script": script,
        "word_count": word_count,
        "estimated_duration_seconds": round(estimated_duration, 1),
        "photo_count": photo_count,
        "property": {
            "id": property.id,
            "address": property.address,
            "city": property.city,
            "price": property.price,
        }
    }


class GenerateVoiceoverRequest(BaseModel):
    """Request to generate voiceover audio only (no video)."""
    property_id: int = Field(..., description="Property ID to generate voiceover for")
    agent_id: int = Field(..., description="Agent ID (for branding context)")
    voice_id: Optional[str] = Field(
        default="21m00Tcm4TlvDq8ikWAM",
        description="ElevenLabs voice ID (default: male voice)"
    )
    output_dir: Optional[str] = Field(
        default="/tmp",
        description="Output directory (default: /tmp)"
    )


class VoiceoverResponse(BaseModel):
    """Response from voiceover generation."""
    audio_path: str
    script: str
    duration_seconds: float
    word_count: int
    property_id: int
    voice_id: str
    audio_size_bytes: int


@router.post("/voiceover", response_model=VoiceoverResponse, status_code=status.HTTP_201_CREATED)
async def generate_voiceover_only(
    request: GenerateVoiceoverRequest,
    db: Session = Depends(get_db)
):
    """
    Generate standalone voiceover audio for a property (no video).

    This endpoint creates ONLY the audio file with ElevenLabs voiceover.
    Use this to:
    - Preview the voiceover before generating full video
    - Generate audio for use in other video editors
    - Test different voices without re-rendering video

    **Parameters:**
    - **property_id**: ID of the property
    - **agent_id**: ID of the agent
    - **voice_id**: Optional ElevenLabs voice ID
    - **output_dir**: Optional output directory

    **Example Request:**
    ```json
    {
      "property_id": 3,
      "agent_id": 5,
      "voice_id": "21m00Tcm4TlvDq8ikWAM"
    }
    ```

    **Returns:**
    - Audio file path
    - Generated script text
    - Audio duration
    - File size
    """
    try:
        from app.models.property import Property
        from app.models.zillow_enrichment import ZillowEnrichment
        import os

        # Fetch property
        property = db.query(Property).filter_by(id=request.property_id).first()
        if not property:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property {request.property_id} not found"
            )

        # Fetch enrichment
        enrichment = db.query(ZillowEnrichment).filter_by(property_id=request.property_id).first()

        # Generate voiceover
        service = PropertyVideoService()

        script = service._generate_script(property, enrichment)

        # Generate audio
        audio_path = await service._generate_voiceover(
            script=script,
            voice_id=request.voice_id,
            output_dir=request.output_dir
        )

        # Get file size
        file_size = os.path.getsize(audio_path) if os.path.exists(audio_path) else 0

        # Calculate duration (word count / 2.5 words per second)
        word_count = len(script.split())
        duration_seconds = word_count / 2.5

        return {
            "audio_path": audio_path,
            "script": script,
            "duration_seconds": round(duration_seconds, 1),
            "word_count": word_count,
            "property_id": request.property_id,
            "voice_id": request.voice_id,
            "audio_size_bytes": file_size
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate voiceover: {str(e)}"
        )
