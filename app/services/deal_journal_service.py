"""Deal Journal Service — logs every interaction and auto-ingests into knowledge base for RAG."""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.deal_journal import DealJournalEntry, JournalEntryType

logger = logging.getLogger(__name__)


class DealJournalService:

    def log_entry(
        self,
        db: Session,
        entry_type: JournalEntryType,
        title: str,
        content: str,
        property_id: int = None,
        contact_id: int = None,
        participants: str = None,
        outcome: str = None,
        follow_up: str = None,
        tags: str = None,
    ) -> DealJournalEntry:
        """Log an interaction and auto-ingest into knowledge base."""

        entry = DealJournalEntry(
            entry_type=entry_type,
            title=title,
            content=content,
            property_id=property_id,
            contact_id=contact_id,
            participants=participants,
            outcome=outcome,
            follow_up=follow_up,
            tags=tags,
        )
        db.add(entry)
        db.flush()

        # Auto-ingest into knowledge base for RAG search
        kb_doc_id = self._ingest_to_knowledge_base(db, entry)
        if kb_doc_id:
            entry.knowledge_doc_id = kb_doc_id

        db.commit()
        db.refresh(entry)
        logger.info(f"Journal entry logged: {title} (type={entry_type.value})")
        return entry

    def search_journal(
        self, db: Session, query: str, property_id: int = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search journal entries. Also searches knowledge base for semantic matches."""

        # Direct DB search
        q = db.query(DealJournalEntry)
        if property_id:
            q = q.filter(DealJournalEntry.property_id == property_id)

        terms = query.split()[:5]
        for term in terms:
            q = q.filter(
                or_(
                    DealJournalEntry.content.ilike(f"%{term}%"),
                    DealJournalEntry.title.ilike(f"%{term}%"),
                    DealJournalEntry.outcome.ilike(f"%{term}%"),
                    DealJournalEntry.tags.ilike(f"%{term}%"),
                )
            )

        entries = q.order_by(DealJournalEntry.created_at.desc()).limit(limit).all()

        # Also search knowledge base for semantic matches
        kb_results = self._search_knowledge_base(db, query, limit)

        results = [self._format_entry(e) for e in entries]

        # Merge KB results (dedupe by knowledge_doc_id)
        existing_kb_ids = {e.knowledge_doc_id for e in entries if e.knowledge_doc_id}
        for kb in kb_results:
            if kb.get("document_id") not in existing_kb_ids:
                results.append({
                    "id": None,
                    "type": "knowledge_base",
                    "title": kb.get("document_title", ""),
                    "content_preview": kb.get("content", "")[:300],
                    "similarity": kb.get("similarity", 0),
                    "source": "knowledge_base_rag",
                })

        return results

    def get_property_journal(
        self, db: Session, property_id: int, limit: int = 50
    ) -> List[Dict]:
        """Get all journal entries for a property."""
        entries = db.query(DealJournalEntry).filter(
            DealJournalEntry.property_id == property_id
        ).order_by(DealJournalEntry.created_at.desc()).limit(limit).all()
        return [self._format_entry(e) for e in entries]

    def get_recent_entries(
        self, db: Session, entry_type: Optional[JournalEntryType] = None, limit: int = 20
    ) -> List[Dict]:
        q = db.query(DealJournalEntry)
        if entry_type:
            q = q.filter(DealJournalEntry.entry_type == entry_type)
        entries = q.order_by(DealJournalEntry.created_at.desc()).limit(limit).all()
        return [self._format_entry(e) for e in entries]

    def _format_entry(self, entry: DealJournalEntry) -> Dict:
        return {
            "id": entry.id,
            "type": entry.entry_type.value,
            "title": entry.title,
            "content_preview": entry.content[:300] if entry.content else "",
            "participants": entry.participants,
            "outcome": entry.outcome,
            "follow_up": entry.follow_up,
            "tags": entry.tags,
            "property_id": entry.property_id,
            "contact_id": entry.contact_id,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
        }

    def _ingest_to_knowledge_base(self, db: Session, entry: DealJournalEntry) -> Optional[int]:
        """Auto-ingest journal entry into knowledge base for RAG."""
        try:
            from app.services.knowledge_base_service import knowledge_base
            from app.models.knowledge_base import DocumentType

            # Build rich text for ingestion
            text_parts = [f"[{entry.entry_type.value.upper()}] {entry.title}"]
            if entry.participants:
                text_parts.append(f"Participants: {entry.participants}")
            text_parts.append(entry.content)
            if entry.outcome:
                text_parts.append(f"Outcome: {entry.outcome}")
            if entry.follow_up:
                text_parts.append(f"Follow-up: {entry.follow_up}")

            full_text = "\n\n".join(text_parts)

            doc = knowledge_base.ingest_text(
                db,
                title=f"Deal Journal: {entry.title}",
                content=full_text,
                doc_type=DocumentType.DEAL_NOTES,
                source=f"deal_journal:{entry.id}",
                metadata={"entry_type": entry.entry_type.value, "property_id": entry.property_id},
            )
            return doc.id
        except Exception as e:
            logger.warning(f"Failed to ingest journal entry to KB: {e}")
            return None

    def _search_knowledge_base(self, db: Session, query: str, limit: int) -> List[Dict]:
        try:
            from app.services.knowledge_base_service import knowledge_base
            from app.models.knowledge_base import DocumentType
            return knowledge_base.search(db, query, limit=limit, doc_type=DocumentType.DEAL_NOTES)
        except Exception:
            return []


deal_journal_service = DealJournalService()
