"""Voice Memo Service — transcribe audio via OpenAI Whisper and ingest into Knowledge Base for RAG."""

import logging
import os
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class VoiceMemoService:
    """Handles voice memo transcription and RAG ingestion."""

    def transcribe_audio(self, file_path: str) -> str:
        """Transcribe an audio file using OpenAI Whisper API.

        Args:
            file_path: Path to the audio file.

        Returns:
            Transcript text.

        Raises:
            RuntimeError: If OPENAI_API_KEY is not set or transcription fails.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set — cannot transcribe audio")
            raise RuntimeError("OPENAI_API_KEY is not configured. Cannot transcribe audio.")

        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)

            with open(file_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                )

            transcript = transcription.text
            logger.info(f"Transcribed audio ({len(transcript)} chars): {transcript[:100]}...")
            return transcript

        except ImportError:
            raise RuntimeError("openai package is not installed. Run: pip install openai")
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise RuntimeError(f"Transcription failed: {e}")

    def process_voice_memo(
        self,
        file_path: str,
        title: str = None,
        property_id: int = None,
        contact_id: int = None,
    ) -> dict:
        """Transcribe audio and ingest transcript into Knowledge Base for RAG search.

        Args:
            file_path: Path to the audio file.
            title: Optional title for the document (defaults to "Voice Memo").
            property_id: Optional property ID to associate with.
            contact_id: Optional contact ID to associate with.

        Returns:
            dict with transcript, document_id, and chunk_count.
        """
        # Step 1: Transcribe
        transcript = self.transcribe_audio(file_path)

        if not title:
            # Use first 60 chars of transcript as title
            title = f"Voice Memo: {transcript[:60]}..." if len(transcript) > 60 else f"Voice Memo: {transcript}"

        # Step 2: Ingest into Knowledge Base
        from app.database import SessionLocal
        from app.services.knowledge_base_service import knowledge_base
        from app.models.knowledge_base import DocumentType

        db = SessionLocal()
        try:
            metadata = {}
            if property_id:
                metadata["property_id"] = property_id
            if contact_id:
                metadata["contact_id"] = contact_id

            doc = knowledge_base.ingest_text(
                db,
                title=title,
                content=transcript,
                doc_type=DocumentType.DEAL_NOTES,
                source="voice_memo",
                metadata=metadata if metadata else None,
            )

            document_id = doc.id
            chunk_count = doc.chunk_count

            # Step 3: Optionally log to Deal Journal if property_id is provided
            if property_id:
                self._log_to_deal_journal(db, transcript, title, property_id, contact_id)

            logger.info(f"Voice memo processed: doc_id={document_id}, chunks={chunk_count}")

            return {
                "transcript": transcript,
                "document_id": document_id,
                "chunk_count": chunk_count,
            }
        finally:
            db.close()

    def process_voice_memo_with_db(
        self,
        db: Session,
        file_path: str,
        title: str = None,
        property_id: int = None,
        contact_id: int = None,
    ) -> dict:
        """Same as process_voice_memo but accepts an existing DB session (for use in routers)."""
        # Step 1: Transcribe
        transcript = self.transcribe_audio(file_path)

        if not title:
            title = f"Voice Memo: {transcript[:60]}..." if len(transcript) > 60 else f"Voice Memo: {transcript}"

        # Step 2: Ingest into Knowledge Base
        from app.services.knowledge_base_service import knowledge_base
        from app.models.knowledge_base import DocumentType

        metadata = {}
        if property_id:
            metadata["property_id"] = property_id
        if contact_id:
            metadata["contact_id"] = contact_id

        doc = knowledge_base.ingest_text(
            db,
            title=title,
            content=transcript,
            doc_type=DocumentType.DEAL_NOTES,
            source="voice_memo",
            metadata=metadata if metadata else None,
        )

        # Step 3: Optionally log to Deal Journal
        if property_id:
            self._log_to_deal_journal(db, transcript, title, property_id, contact_id)

        logger.info(f"Voice memo processed: doc_id={doc.id}, chunks={doc.chunk_count}")

        return {
            "transcript": transcript,
            "document_id": doc.id,
            "chunk_count": doc.chunk_count,
        }

    def _log_to_deal_journal(
        self,
        db: Session,
        transcript: str,
        title: str,
        property_id: int,
        contact_id: int = None,
    ):
        """Log the voice memo transcript to the Deal Journal."""
        try:
            from app.services.deal_journal_service import deal_journal_service
            from app.models.deal_journal import JournalEntryType

            deal_journal_service.log_entry(
                db,
                entry_type=JournalEntryType.NOTE,
                title=title,
                content=transcript,
                property_id=property_id,
                contact_id=contact_id,
                tags="voice_memo",
            )
            logger.info(f"Voice memo logged to deal journal for property {property_id}")
        except Exception as e:
            logger.warning(f"Failed to log voice memo to deal journal: {e}")


# Global instance
voice_memo_service = VoiceMemoService()
