from pydantic import BaseModel
from datetime import datetime

from app.models.property_note import NoteSource


class NoteCreate(BaseModel):
    property_id: int
    content: str
    source: NoteSource = NoteSource.MANUAL
    created_by: str | None = None


class NoteResponse(BaseModel):
    id: int
    property_id: int
    content: str
    source: NoteSource
    created_by: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class NoteListResponse(BaseModel):
    notes: list[NoteResponse]
    voice_summary: str
