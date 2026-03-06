"""Knowledge Base model — documents and chunks for RAG."""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from app.database import Base

try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False


class DocumentType(str, enum.Enum):
    PDF = "pdf"
    CONTRACT = "contract"
    DEAL_NOTES = "deal_notes"
    MARKET_REPORT = "market_report"
    EMAIL = "email"
    MEETING_NOTES = "meeting_notes"
    PLAIN_TEXT = "plain_text"
    WEBPAGE = "webpage"


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    source = Column(String(1000))  # file path, URL, or identifier
    doc_type = Column(SAEnum(DocumentType), default=DocumentType.PLAIN_TEXT)
    content = Column(Text)  # full raw text
    metadata_json = Column(Text)  # JSON string for extra metadata
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)  # order within document
    content = Column(Text, nullable=False)
    token_count = Column(Integer)
    embedding = Column(Vector(1536)) if HAS_PGVECTOR else Column(Text)  # OpenAI ada-002 dimensions
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    document = relationship("KnowledgeDocument", back_populates="chunks")
