"""Voice Memo API — upload audio, transcribe via Whisper, and ingest into RAG."""

import logging
import os
import tempfile

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.voice_memo_service import voice_memo_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice-memo", tags=["Voice Memo"])


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
):
    """Upload an audio file and get the transcript back.

    Supports common audio formats: mp3, wav, m4a, ogg, webm, mp4, flac.
    """
    # Save uploaded file to temp location
    suffix = _get_file_suffix(file.filename)
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        transcript = voice_memo_service.transcribe_audio(tmp_path)
        return {
            "transcript": transcript,
            "filename": file.filename,
            "message": "Audio transcribed successfully",
        }
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/process")
async def process_voice_memo(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    property_id: Optional[int] = Form(None),
    contact_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    """Upload an audio file, transcribe it, and ingest the transcript into the Knowledge Base for RAG search.

    Optionally associate with a property or contact. If property_id is provided,
    the transcript is also logged to the Deal Journal.
    """
    suffix = _get_file_suffix(file.filename)
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        result = voice_memo_service.process_voice_memo_with_db(
            db=db,
            file_path=tmp_path,
            title=title,
            property_id=property_id,
            contact_id=contact_id,
        )
        return {
            "transcript": result["transcript"],
            "document_id": result["document_id"],
            "chunk_count": result["chunk_count"],
            "message": f"Voice memo transcribed and ingested — {result['chunk_count']} chunks created",
        }
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def _get_file_suffix(filename: str | None) -> str:
    """Extract file extension from filename, defaulting to .wav."""
    if filename and "." in filename:
        return "." + filename.rsplit(".", 1)[-1].lower()
    return ".wav"
