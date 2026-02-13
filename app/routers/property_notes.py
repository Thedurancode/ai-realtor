"""Property notes endpoints for adding freeform notes to properties."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.property import Property
from app.models.property_note import PropertyNote, NoteSource
from app.schemas.property_note import NoteCreate, NoteResponse, NoteListResponse
from app.services.property_recap_service import regenerate_recap_background

router = APIRouter(prefix="/property-notes", tags=["property-notes"])


@router.post("/", response_model=NoteResponse, status_code=201)
async def create_note(note: NoteCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Add a note to a property."""
    prop = db.query(Property).filter(Property.id == note.property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    new_note = PropertyNote(
        property_id=note.property_id,
        content=note.content,
        source=note.source,
        created_by=note.created_by,
    )
    db.add(new_note)
    db.commit()
    db.refresh(new_note)

    background_tasks.add_task(regenerate_recap_background, note.property_id, "note_added")
    return new_note


@router.get("/property/{property_id}", response_model=NoteListResponse)
def list_notes(property_id: int, limit: int = 20, db: Session = Depends(get_db)):
    """List notes for a property, most recent first."""
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    notes = (
        db.query(PropertyNote)
        .filter(PropertyNote.property_id == property_id)
        .order_by(PropertyNote.created_at.desc())
        .limit(limit)
        .all()
    )

    if not notes:
        voice_summary = f"No notes for {prop.address}."
    elif len(notes) == 1:
        voice_summary = f"1 note for {prop.address}: {notes[0].content[:100]}"
    else:
        voice_summary = f"{len(notes)} notes for {prop.address}. Most recent: {notes[0].content[:100]}"

    return NoteListResponse(notes=notes, voice_summary=voice_summary)


@router.delete("/{note_id}", status_code=204)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    """Delete a note."""
    note = db.query(PropertyNote).filter(PropertyNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    return None
