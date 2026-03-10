"""
Voice Agent Router

VAPI webhook endpoints, call management, and voice memo processing.
Handles inbound calls, speech processing, outbound call initiation, and audio transcription.
"""
import hashlib
import hmac
import json
import logging
import os
import tempfile
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.services.voice_agent_service import voice_agent_service
from app.services.voice_memo_service import voice_memo_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice/agent", tags=["voice-agent"])


# ── Request Models ──

class OutboundCallRequest(BaseModel):
    phone_number: str  # E.164 format: +14155551234


# ── VAPI Webhook ──

def _verify_vapi_signature(request_body: bytes, signature: str) -> bool:
    """Verify VAPI webhook signature if secret is configured."""
    if not settings.vapi_webhook_secret:
        return True  # Skip verification if no secret configured
    expected = hmac.new(
        settings.vapi_webhook_secret.encode(),
        request_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/vapi/webhook")
async def vapi_webhook(request: Request):
    """
    VAPI webhook endpoint.

    Handles events:
    - call.started: New call initiated
    - call.speech: User speech transcribed
    - call.ended: Call completed
    - call.function_call: VAPI detected a function call
    """
    body = await request.body()

    # Verify signature if configured
    signature = request.headers.get("x-vapi-signature", "")
    if settings.vapi_webhook_secret and not _verify_vapi_signature(body, signature):
        logger.warning("VAPI webhook signature verification failed")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = payload.get("message", {}).get("type", payload.get("type", ""))
    call_data = payload.get("message", {}).get("call", payload.get("call", {}))
    call_id = call_data.get("id", payload.get("call_id", ""))

    logger.info(f"VAPI webhook event: {event_type} for call {call_id}")

    if event_type in ("call.started", "assistant-request"):
        result = await voice_agent_service.handle_call_start(call_data)
        return result

    elif event_type in ("call.speech", "transcript", "conversation-update"):
        transcript = (
            payload.get("message", {}).get("transcript", "")
            or payload.get("transcript", "")
        )
        if not transcript:
            return {"status": "ok", "message": "No transcript provided"}
        result = await voice_agent_service.handle_speech(call_id, transcript)
        return result

    elif event_type in ("call.function_call", "function-call"):
        function_call = payload.get("message", {}).get("functionCall", payload.get("functionCall", {}))
        function_name = function_call.get("name", "")
        arguments = function_call.get("parameters", function_call.get("arguments", {}))
        if isinstance(arguments, str):
            arguments = json.loads(arguments)
        result = await voice_agent_service.handle_function_call(call_id, function_name, arguments)
        return {"result": result}

    elif event_type in ("call.ended", "end-of-call-report"):
        result = await voice_agent_service.handle_call_end(call_data)
        return result

    elif event_type == "hang":
        # VAPI hang notification
        result = await voice_agent_service.handle_call_end(call_data)
        return result

    else:
        logger.debug(f"Unhandled VAPI event type: {event_type}")
        return {"status": "ok", "message": f"Event {event_type} acknowledged"}


# ── Call Management ──

@router.post("/call")
async def initiate_outbound_call(request_data: OutboundCallRequest):
    """
    Initiate an outbound voice agent call via VAPI.

    Phone number must be in E.164 format: +14155551234
    """
    try:
        result = await voice_agent_service.initiate_outbound_call(request_data.phone_number)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to initiate outbound call: {e}")
        raise HTTPException(status_code=500, detail=f"Call initiation failed: {str(e)}")


@router.get("/calls")
async def list_voice_calls(limit: int = 20):
    """List recent voice agent calls."""
    return voice_agent_service.list_call_records(limit=limit)


@router.get("/calls/{call_id}")
async def get_voice_call(call_id: str):
    """Get transcript and actions for a specific voice agent call."""
    record = voice_agent_service.get_call_record(call_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Call {call_id} not found")
    return record


# ── Voice Memo (merged from voice_memo.py) ──────────────────────

_memo_router = APIRouter(prefix="/voice-memo", tags=["Voice Memo"])


def _get_file_suffix(filename: str | None) -> str:
    """Extract file extension from filename, defaulting to .wav."""
    if filename and "." in filename:
        return "." + filename.rsplit(".", 1)[-1].lower()
    return ".wav"


@_memo_router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Upload an audio file and get the transcript back."""
    suffix = _get_file_suffix(file.filename)
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        transcript = voice_memo_service.transcribe_audio(tmp_path)
        return {"transcript": transcript, "filename": file.filename, "message": "Audio transcribed successfully"}
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@_memo_router.post("/process")
async def process_voice_memo(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    property_id: Optional[int] = Form(None),
    contact_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    """Upload audio, transcribe, and ingest into Knowledge Base for RAG search."""
    suffix = _get_file_suffix(file.filename)
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        result = voice_memo_service.process_voice_memo_with_db(
            db=db, file_path=tmp_path, title=title, property_id=property_id, contact_id=contact_id,
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
