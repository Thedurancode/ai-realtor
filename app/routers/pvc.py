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

from fastapi import APIRouter, HTTPException, Depends, UploadFile
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone

from app.services.pvc_service import PVCService
from app.services.resend_service import resend_service
from app.database import get_db
from app.models.pvc_voice import PVCVoice, PVCVoiceStatus
from app.schemas.pvc import (
    PVCVoiceResponse,
    CreatePVCVoiceRequest,
    UploadPVCSamplesRequest,
    PVCSamplesResponse,
    StartSpeakerSeparationRequest,
    SpeakerSeparationResponse,
    PVCStatusResponse,
    ListPVCVoicesResponse,
)
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.config import settings

router = APIRouter(prefix="/v1/pvc", tags=["PVC", "Voices"])

# Endpoints
@router.post("/voices", response_model=PVCVoiceResponse)
async def create_pvc_voice(
    request: CreatePVCVoiceRequest,
    db: Session = Depends(get_db),
):
    """
    Create a new Professional Voice Clone.
    """
    service = PVCService(api_key=settings.elevenlabs_api_key)

    try:
        result = await service.create_pvc_voice(
            name=request.name,
            language=request.language,
            description=request.description,
        )

        # Save to database
        pvc_voice = PVCVoice(
            id=result["voice_id"],
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


@router.post("/voices/{voice_id}/samples/speakers", response_model=SpeakerSeparationResponse)
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
    Sends email notification when voice becomes ready.
    """
    service = PVCService(api_key=settings.elevenlabs_api_key)

    try:
        result = await service.get_pvc_status(voice_id=voice_id)
        new_status = result.get("status")

        # Update database with latest status
        pvc_voice = db.query(PVCVoice).filter(PVCVoice.id == voice_id).first()
        if pvc_voice:
            old_status = pvc_voice.status
            pvc_voice.status = new_status
            pvc_voice.updated_at = datetime.now(timezone.utc)

            # Update additional fields if provided
            if "speakers_count" in result:
                pvc_voice.speakers_count = result.get("speakers_count")
            if "model_id" in result:
                pvc_voice.model_id = result.get("model_id")
            if "is_trained" in result:
                pvc_voice.is_trained = result.get("is_trained", False)
            if pvc_voice.is_trained and not pvc_voice.trained_at:
                pvc_voice.trained_at = datetime.now(timezone.utc)

            db.commit()

            # Send email notification when voice becomes ready
            if old_status != "ready" and new_status == "ready":
                # Calculate training time
                training_time = "Unknown"
                if pvc_voice.created_at:
                    duration = datetime.now(timezone.utc) - pvc_voice.created_at
                    hours = duration.total_seconds() / 3600
                    if hours < 1:
                        training_time = f"{int(duration.total_seconds() / 60)} minutes"
                    else:
                        training_time = f"{int(hours)} hours"

                # Send notification email
                email_result = resend_service.send_pvc_voice_ready_notification(
                    to_email=settings.admin_email,
                    to_name=settings.admin_name,
                    voice_id=voice_id,
                    voice_name=pvc_voice.name,
                    language=pvc_voice.language,
                    sample_count=pvc_voice.sample_count,
                    training_time=training_time,
                )

                # Log the notification
                print(f"✅ PVC voice ready notification sent to {settings.admin_email}: {email_result}")

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
        pvc_voice = db.query(PVCVoice).filter(PVCVoice.id == voice_id).first()
        if pvc_voice:
            db.delete(pvc_voice)
            db.commit()

            return {"voice_id": voice_id, "deleted": True}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
