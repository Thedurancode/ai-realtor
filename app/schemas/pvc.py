"""Pydantic models for PVC (Professional Voice Clone) API"""

from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime


class PVCVoiceResponse(BaseModel):
    """Response for PVC voice operations"""
    voice_id: str
    name: str
    language: str
    description: Optional[str]
    status: str
    created_at: Optional[str]
    sample_ids: List[str]
    sample_count: int
    speakers_count: Optional[int]
    model_id: Optional[str]
    training_progress: Optional[str]
    is_trained: bool
    trained_at: Optional[str]


class ListPVCVoicesResponse(BaseModel):
    """Response for listing all PVC voices"""
    voices: List[PVCVoiceResponse]


class PVCSamplesResponse(BaseModel):
    """Response for sample upload"""
    voice_id: str
    sample_ids: List[str]
    upload_count: int


class SpeakerSeparationResponse(BaseModel):
    """Response for speaker separation"""
    voice_id: str
    status: str
    sample_count: int


class PVCStatusResponse(BaseModel):
    """Response for PVC status"""
    voice_id: str
    name: str
    language: str
    description: Optional[str]
    status: str
    created_at: Optional[str]
    updated_at: Optional[str]
    sample_count: int
    speakers_count: Optional[int]
    model_id: Optional[str]
    training_progress: Optional[str]
    is_trained: bool
    trained_at: Optional[str]
    metadata: Optional[dict]
