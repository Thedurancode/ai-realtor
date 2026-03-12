"""Deal Journal API — log and search every deal interaction."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models.deal_journal import JournalEntryType
from app.services.deal_journal_service import deal_journal_service

router = APIRouter(prefix="/journal", tags=["Deal Journal"])


class LogEntryRequest(BaseModel):
    entry_type: str  # call, email, showing, meeting, offer, negotiation, inspection, note
    title: str
    content: str
    property_id: Optional[int] = None
    contact_id: Optional[int] = None
    participants: Optional[str] = None
    outcome: Optional[str] = None
    follow_up: Optional[str] = None
    tags: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    property_id: Optional[int] = None
    limit: int = 10


@router.post("/log")
async def log_entry(req: LogEntryRequest, db: Session = Depends(get_db)):
    """Log an interaction (call, email, showing, meeting, etc.) to the deal journal."""
    try:
        entry_type = JournalEntryType(req.entry_type)
    except ValueError:
        raise HTTPException(400, f"Invalid entry type. Use: {[e.value for e in JournalEntryType]}")

    entry = deal_journal_service.log_entry(
        db, entry_type=entry_type, title=req.title, content=req.content,
        property_id=req.property_id, contact_id=req.contact_id,
        participants=req.participants, outcome=req.outcome,
        follow_up=req.follow_up, tags=req.tags,
    )
    return {"message": f"Logged to deal journal", "id": entry.id, "kb_doc_id": entry.knowledge_doc_id}


@router.post("/search")
async def search_journal(req: SearchRequest, db: Session = Depends(get_db)):
    """Search the deal journal using keywords + knowledge base RAG."""
    results = deal_journal_service.search_journal(db, query=req.query, property_id=req.property_id, limit=req.limit)
    return {"query": req.query, "count": len(results), "results": results}


@router.get("/property/{property_id}")
async def get_property_journal(property_id: int, limit: int = 50, db: Session = Depends(get_db)):
    """Get all journal entries for a property."""
    entries = deal_journal_service.get_property_journal(db, property_id, limit=limit)
    return {"property_id": property_id, "count": len(entries), "entries": entries}


@router.get("/recent")
async def get_recent_entries(entry_type: Optional[str] = None, limit: int = 20, db: Session = Depends(get_db)):
    """Get recent journal entries."""
    et = None
    if entry_type:
        try:
            et = JournalEntryType(entry_type)
        except ValueError:
            raise HTTPException(400, f"Invalid type. Use: {[e.value for e in JournalEntryType]}")
    entries = deal_journal_service.get_recent_entries(db, entry_type=et, limit=limit)
    return {"count": len(entries), "entries": entries}
