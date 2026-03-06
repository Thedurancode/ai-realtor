"""Knowledge Base API — ingest, search, and manage documents for RAG."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import os
import tempfile

from app.database import get_db
from app.models.knowledge_base import DocumentType
from app.services.knowledge_base_service import knowledge_base

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])


class IngestTextRequest(BaseModel):
    title: str
    content: str
    doc_type: DocumentType = DocumentType.PLAIN_TEXT
    source: Optional[str] = None
    metadata: Optional[dict] = None


class IngestURLRequest(BaseModel):
    url: str
    title: Optional[str] = None
    metadata: Optional[dict] = None


class SearchRequest(BaseModel):
    query: str
    limit: int = 5
    doc_type: Optional[DocumentType] = None


# ── Ingest ──

@router.post("/ingest/text")
async def ingest_text(req: IngestTextRequest, db: Session = Depends(get_db)):
    """Ingest plain text, deal notes, contracts, or any text content."""
    doc = knowledge_base.ingest_text(
        db, title=req.title, content=req.content,
        doc_type=req.doc_type, source=req.source, metadata=req.metadata,
    )
    return {
        "id": doc.id,
        "title": doc.title,
        "chunk_count": doc.chunk_count,
        "message": f"Ingested '{doc.title}' — {doc.chunk_count} chunks created and embedded",
    }


@router.post("/ingest/pdf")
async def ingest_pdf(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    doc_type: DocumentType = Form(DocumentType.PDF),
    db: Session = Depends(get_db),
):
    """Upload and ingest a PDF document."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "File must be a PDF")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        doc = knowledge_base.ingest_pdf(
            db, file_path=tmp_path,
            title=title or file.filename, doc_type=doc_type,
        )
        return {
            "id": doc.id,
            "title": doc.title,
            "chunk_count": doc.chunk_count,
            "message": f"Ingested PDF '{doc.title}' — {doc.chunk_count} chunks",
        }
    finally:
        os.unlink(tmp_path)


@router.post("/ingest/url")
async def ingest_url(req: IngestURLRequest, db: Session = Depends(get_db)):
    """Fetch and ingest a webpage."""
    doc = knowledge_base.ingest_webpage(
        db, url=req.url, title=req.title, metadata=req.metadata,
    )
    return {
        "id": doc.id,
        "title": doc.title,
        "chunk_count": doc.chunk_count,
        "message": f"Ingested webpage '{doc.title}' — {doc.chunk_count} chunks",
    }


# ── Search ──

@router.post("/search")
async def search_knowledge(req: SearchRequest, db: Session = Depends(get_db)):
    """Semantic search across all documents in the knowledge base."""
    results = knowledge_base.search(
        db, query=req.query, limit=req.limit, doc_type=req.doc_type,
    )
    return {
        "query": req.query,
        "count": len(results),
        "results": results,
    }


# ── Management ──

@router.get("/documents")
async def list_documents(
    doc_type: Optional[DocumentType] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List all documents in the knowledge base."""
    docs = knowledge_base.list_documents(db, doc_type=doc_type, limit=limit)
    return {
        "count": len(docs),
        "documents": [
            {
                "id": d.id,
                "title": d.title,
                "doc_type": d.doc_type.value if d.doc_type else None,
                "source": d.source,
                "chunk_count": d.chunk_count,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in docs
        ],
    }


@router.get("/documents/{doc_id}")
async def get_document(doc_id: int, db: Session = Depends(get_db)):
    """Get a document with its full content."""
    doc = knowledge_base.get_document(db, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    return {
        "id": doc.id,
        "title": doc.title,
        "doc_type": doc.doc_type.value if doc.doc_type else None,
        "source": doc.source,
        "content": doc.content,
        "chunk_count": doc.chunk_count,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: int, db: Session = Depends(get_db)):
    """Delete a document and all its chunks."""
    if not knowledge_base.delete_document(db, doc_id):
        raise HTTPException(404, "Document not found")
    return {"message": f"Document {doc_id} deleted"}
