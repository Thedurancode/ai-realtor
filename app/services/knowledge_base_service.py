"""Knowledge Base RAG Service — ingest, chunk, embed, and search documents."""

import json
import logging
import os
import re
from typing import List, Optional, Dict, Any

import httpx
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.knowledge_base import KnowledgeDocument, KnowledgeChunk, DocumentType

logger = logging.getLogger(__name__)

# Chunking config
CHUNK_SIZE = 800  # tokens (roughly 4 chars per token)
CHUNK_OVERLAP = 100
CHARS_PER_TOKEN = 4


class KnowledgeBaseService:
    """Handles document ingestion, chunking, embedding, and semantic search."""

    def __init__(self):
        self._openai_key = None

    @property
    def openai_key(self) -> str:
        if not self._openai_key:
            from app.config import settings
            self._openai_key = settings.openai_api_key
        return self._openai_key

    # ── Ingestion ──

    def ingest_text(
        self,
        db: Session,
        title: str,
        content: str,
        doc_type: DocumentType = DocumentType.PLAIN_TEXT,
        source: str = None,
        metadata: dict = None,
    ) -> KnowledgeDocument:
        """Ingest plain text into the knowledge base."""
        doc = KnowledgeDocument(
            title=title,
            source=source or "",
            doc_type=doc_type,
            content=content,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        db.add(doc)
        db.flush()

        chunks = self._chunk_text(content)
        embeddings = self._embed_texts(chunks)

        for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            chunk = KnowledgeChunk(
                document_id=doc.id,
                chunk_index=i,
                content=chunk_text,
                token_count=len(chunk_text) // CHARS_PER_TOKEN,
                embedding=embedding,
            )
            db.add(chunk)

        doc.chunk_count = len(chunks)
        db.commit()
        db.refresh(doc)
        logger.info(f"Ingested document '{title}' — {len(chunks)} chunks")
        return doc

    def ingest_pdf(
        self,
        db: Session,
        file_path: str,
        title: str = None,
        doc_type: DocumentType = DocumentType.PDF,
        metadata: dict = None,
    ) -> KnowledgeDocument:
        """Extract text from a PDF and ingest it."""
        text_content = self._extract_pdf_text(file_path)
        if not title:
            title = os.path.basename(file_path)
        return self.ingest_text(
            db, title=title, content=text_content,
            doc_type=doc_type, source=file_path, metadata=metadata,
        )

    def ingest_webpage(
        self,
        db: Session,
        url: str,
        title: str = None,
        metadata: dict = None,
    ) -> KnowledgeDocument:
        """Fetch and ingest a webpage."""
        text_content = self._fetch_webpage_text(url)
        if not title:
            title = url[:200]
        return self.ingest_text(
            db, title=title, content=text_content,
            doc_type=DocumentType.WEBPAGE, source=url, metadata=metadata,
        )

    # ── Search ──

    def search(
        self,
        db: Session,
        query: str,
        limit: int = 5,
        doc_type: Optional[DocumentType] = None,
    ) -> List[Dict[str, Any]]:
        """Semantic search across all knowledge base chunks."""
        query_embedding = self._embed_texts([query])[0]

        if query_embedding is None:
            return self._fallback_keyword_search(db, query, limit, doc_type)

        # pgvector cosine distance search
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        sql = """
            SELECT
                kc.id,
                kc.content,
                kc.document_id,
                kd.title,
                kd.doc_type,
                kd.source,
                (kc.embedding <=> :embedding::vector) AS distance
            FROM knowledge_chunks kc
            JOIN knowledge_documents kd ON kd.id = kc.document_id
        """
        params = {"embedding": embedding_str, "limit": limit}

        if doc_type:
            sql += " WHERE kd.doc_type = :doc_type"
            params["doc_type"] = doc_type.value

        sql += " ORDER BY kc.embedding <=> :embedding::vector LIMIT :limit"

        rows = db.execute(text(sql), params).fetchall()

        results = []
        for row in rows:
            similarity = 1 - row.distance  # cosine distance → similarity
            results.append({
                "chunk_id": row.id,
                "content": row.content,
                "document_id": row.document_id,
                "document_title": row.title,
                "doc_type": row.doc_type,
                "source": row.source,
                "similarity": round(similarity, 4),
            })

        return results

    def get_document(self, db: Session, doc_id: int) -> Optional[KnowledgeDocument]:
        return db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()

    def list_documents(
        self,
        db: Session,
        doc_type: Optional[DocumentType] = None,
        limit: int = 50,
    ) -> List[KnowledgeDocument]:
        q = db.query(KnowledgeDocument)
        if doc_type:
            q = q.filter(KnowledgeDocument.doc_type == doc_type)
        return q.order_by(KnowledgeDocument.created_at.desc()).limit(limit).all()

    def delete_document(self, db: Session, doc_id: int) -> bool:
        doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
        if not doc:
            return False
        db.delete(doc)
        db.commit()
        return True

    # ── Chunking ──

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        # Clean up whitespace
        text = re.sub(r'\n{3,}', '\n\n', text.strip())

        char_chunk = CHUNK_SIZE * CHARS_PER_TOKEN
        char_overlap = CHUNK_OVERLAP * CHARS_PER_TOKEN

        if len(text) <= char_chunk:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + char_chunk

            # Try to break at paragraph or sentence boundary
            if end < len(text):
                # Look for paragraph break
                para_break = text.rfind('\n\n', start + char_chunk // 2, end)
                if para_break > start:
                    end = para_break
                else:
                    # Look for sentence break
                    sent_break = text.rfind('. ', start + char_chunk // 2, end)
                    if sent_break > start:
                        end = sent_break + 1

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - char_overlap
            if start >= len(text):
                break

        return chunks

    # ── Embeddings ──

    def _embed_texts(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings via OpenAI API."""
        if not self.openai_key:
            logger.warning("No OPENAI_API_KEY — skipping embeddings, using keyword search only")
            return [None] * len(texts)

        try:
            response = httpx.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {self.openai_key}"},
                json={
                    "model": "text-embedding-3-small",
                    "input": [t[:8000] for t in texts],  # truncate to model limit
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return [item["embedding"] for item in data["data"]]
        except Exception as e:
            logger.error(f"Embedding API call failed: {e}")
            return [None] * len(texts)

    # ── PDF Extraction ──

    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from a PDF file."""
        try:
            from fpdf2 import FPDF
        except ImportError:
            pass

        # Try pdfplumber first (best quality)
        try:
            import pdfplumber
            text_parts = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            return "\n\n".join(text_parts)
        except ImportError:
            pass

        # Fallback to PyPDF2
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            return "\n\n".join(text_parts)
        except ImportError:
            pass

        raise RuntimeError("No PDF library available. Install pdfplumber or PyPDF2.")

    # ── Webpage Fetching ──

    def _fetch_webpage_text(self, url: str) -> str:
        """Fetch and extract text from a webpage."""
        from bs4 import BeautifulSoup

        response = httpx.get(url, follow_redirects=True, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        # Remove scripts and styles
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        return soup.get_text(separator="\n", strip=True)

    # ── Fallback Search ──

    def _fallback_keyword_search(
        self, db: Session, query: str, limit: int, doc_type: Optional[DocumentType]
    ) -> List[Dict[str, Any]]:
        """Simple keyword search when embeddings aren't available."""
        q = db.query(KnowledgeChunk).join(KnowledgeDocument)

        if doc_type:
            q = q.filter(KnowledgeDocument.doc_type == doc_type)

        # Basic ILIKE search
        terms = query.split()
        for term in terms[:5]:
            q = q.filter(KnowledgeChunk.content.ilike(f"%{term}%"))

        chunks = q.limit(limit).all()

        return [
            {
                "chunk_id": c.id,
                "content": c.content,
                "document_id": c.document_id,
                "document_title": c.document.title,
                "doc_type": c.document.doc_type.value if c.document.doc_type else None,
                "source": c.document.source,
                "similarity": 0.5,  # placeholder
            }
            for c in chunks
        ]


# Global instance
knowledge_base = KnowledgeBaseService()
