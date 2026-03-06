"""Deal Journal model — auto-logs every interaction for RAG retrieval."""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.sql import func
import enum

from app.database import Base


class JournalEntryType(str, enum.Enum):
    CALL = "call"
    EMAIL = "email"
    SHOWING = "showing"
    MEETING = "meeting"
    OFFER = "offer"
    NEGOTIATION = "negotiation"
    INSPECTION = "inspection"
    APPRAISAL = "appraisal"
    CLOSING = "closing"
    NOTE = "note"


class DealJournalEntry(Base):
    __tablename__ = "deal_journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True, index=True)

    entry_type = Column(SAEnum(JournalEntryType), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)  # Full details of the interaction
    participants = Column(String(500), nullable=True)  # Who was involved
    outcome = Column(String(500), nullable=True)  # What was decided/agreed
    follow_up = Column(String(500), nullable=True)  # Next steps
    tags = Column(String(500), nullable=True)  # Comma-separated tags

    # Link to knowledge base (auto-ingested for RAG)
    knowledge_doc_id = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
