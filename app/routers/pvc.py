"""PVC (Professional Voice Clone) API Router
FastAPI endpoints for voice cloning with ElevenLabs PVC API.

Endpoints:
- POST   /v1/pvc/voices              - Create PVC voice
- POST   /v1/pvc/voices/{id}/samples - Upload samples
- POST   /v1/pvc/voices/{id}/samples/speakers - Start separation
- GET    /v1/pvc/voices/{id}        - Get voice status
- GET    /v1/pvc/voices                  - List all PVC voices
- DELETE /v1/pvc/voices/{id}           - Delete PVC voice
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional

from app.services.pvc_service import PVCService
from app.database import get_db
from app.models.pvc_voice import PVCVoice, PVCVoiceStatus
from sqlalchemy.orm import Session
from sqlalchemy import desc

router = APIRouter(prefix="/v1/pvc", tags=["PVC", "Voices"])


# Pydantic models
class CreatePVCVoiceRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    language: str = Field(default="en", pattern="^[a-z]{2,3}$")
    description: Optional[str] = Field(default=None, max_length=500)


class UploadPVCSamplesRequest(BaseModel):
    file_paths: List[str] = Field(..., min_items=1, max_items=10)


class StartSpeakerSeparationRequest(BaseModel):
    sample_ids: List[str] = Field(..., min_items=1)


# Endpoints
@router.post("/voices", response_model=PVCVoiceResponse)
async def create_pvc_voice(
    request: CreatePVCVoiceRequest,
    db: Session = Depends(get_db),
):
    """
    Create a new Professional Voice Clone.
    """
    service = PVCService()

    try:
        result = await service.create_pvc_voice(
            name=request.name,
            language=request.language,
            description=request.description,
        )

        # Save to database
        pvc_voice = PVCVoice(
            voice_id=result["voice_id"],
            name=result["name"],
            language=result["language"],
            description=result.get("description"),
            status=PVCVoiceStatus.PROCESSING,
            created_at=result.get("created_at"),
        )
        db.add(pvc_voice)
        db.commit()

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voices/{voice_id}/samples", response_model=PVCVoiceResponse)
async def upload_pvc_samples(
    voice_id: str,
    request: UploadPVCSamplesRequest,
    db: Session = Depends(get_db),
):
    """
    Upload audio samples for training a PVC voice.
    """
    service = PVCService()

    try:
        result = await service.upload_pvc_samples(
            voice_id=voice_id,
            file_paths=request.file_paths,
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voices/{voice_id}/samples/speakers", response_model=PVCVoiceResponse)
async def start_speaker_separation(
    voice_id: str,
    request: StartSpeakerSeparationRequest,
    db: Session = Depends(get_db),
):
    """
    Start speaker separation for uploaded samples.
    """
    service = PVCService()

    try:
        result = await service.start_speaker_separation(
            voice_id=voice_id,
            sample_ids=request.sample_ids,
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voices/{voice_id}", response_model=PVCVoiceResponse)
async def get_pvc_voice_status(
    voice_id: str,
    db: Session = Depends(get_db),
):
    """
    Get current status of a PVC voice.
    """
    service = PVCService()

    try:
        result = await service.get_pvc_status(voice_id=voice_id)

        # Update database with latest status
        pvc_voice = db.query(PVCVoice).filter(PVCVoice.voice_id == voice_id).first()
        if pvc_voice:
            pvc_voice.status = result.get("status")
            pvc_voice.updated_at = datetime.now(timezone.utc)
            db.commit()

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voices", response_model=List[PVCVoiceResponse])
async def list_pvc_voices(db: Session = Depends(get_db)):
    """
    Get all PVC voices for the account.
    """
    service = PVCService()

    try:
        voices = await service.get_pvc_voices()

        return {"voices": voices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/voices/{voice_id}")
async def delete_pvc_voice(
    voice_id: str,
    db: Session = Depends(get_db),
):
    """
    Delete a PVC voice.
    """
    service = PVCService()

    try:
        # In a real implementation, this would call the ElevenLabs API to delete
        # For now, just mark as deleted in database
        pvc_voice = db.query(PVCVoice).filter(PVCVoice.voice_id == voice_id).first()
        if pvc_voice:
            db.delete(pvc_voice)
            db.commit()

            return {"voice_id": voice_id, "deleted": True}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
