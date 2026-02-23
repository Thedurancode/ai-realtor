"""Hybrid search API router."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.database import get_db
from app.services.hybrid_search import hybrid_search
from app.models.property import Property

router = APIRouter(prefix="/search", tags=["Hybrid Search"])


class SearchResult(BaseModel):
    property_id: int
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    price: Optional[float]
    fts_score: float
    vector_score: float
    combined_score: float


@router.get("/properties")
async def search_properties(
    q: str = Query(..., description="Search query"),
    workspace_id: Optional[int] = Query(None),
    agent_id: Optional[int] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    use_semantic: bool = Query(True, description="Include vector search"),
    db: Session = Depends(get_db)
):
    """Hybrid search: FTS5 + vector similarity.

    Combines full-text search with semantic vector search for optimal results.
    No external vector database required.
    """
    try:
        results = hybrid_search.search_properties(
            db=db,
            query=q,
            workspace_id=workspace_id,
            agent_id=agent_id,
            limit=limit,
            use_semantic=use_semantic
        )

        return {
            "query": q,
            "total_results": len(results),
            "results": [
                {
                    "property_id": r["property"].id,
                    "address": r["property"].address,
                    "city": r["property"].city,
                    "state": r["property"].state,
                    "price": r["property"].price,
                    "bedrooms": r["property"].bedrooms,
                    "bathrooms": r["property"].bathrooms,
                    "square_feet": r["property"].square_feet,
                    "property_type": r["property"].property_type.value if r["property"].property_type else None,
                    "status": r["property"].status.value if r["property"].status else None,
                    "deal_score": r["property"].deal_score,
                    "score_grade": r["property"].score_grade,
                    "fts_score": r["fts_score"],
                    "vector_score": r["vector_score"],
                    "combined_score": r["combined_score"]
                }
                for r in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similar/{property_id}")
async def find_similar_properties(
    property_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Find properties similar to a given property using vector search.

    Uses vector embeddings to find semantically similar properties.
    """
    try:
        similar_properties = hybrid_search.search_similar_properties(
            db=db,
            property_id=property_id,
            limit=limit
        )

        return {
            "reference_property_id": property_id,
            "similar_count": len(similar_properties),
            "similar_properties": [
                {
                    "property_id": p.id,
                    "address": p.address,
                    "city": p.city,
                    "state": p.state,
                    "price": p.price,
                    "bedrooms": p.bedrooms,
                    "bathrooms": p.bathrooms,
                    "square_feet": p.square_feet,
                    "property_type": p.property_type.value if p.property_type else None,
                    "deal_score": p.deal_score,
                    "score_grade": p.score_grade
                }
                for p in similar_properties
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index/{property_id}")
async def index_property(
    property_id: int,
    db: Session = Depends(get_db)
):
    """Manually trigger indexing for a property.

    Updates both FTS5 full-text search and vector embeddings.
    """
    from app.models.property import Property

    prop = db.query(Property).filter(Property.id == property_id).first()

    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    try:
        # Prepare text for FTS5
        text = f"{prop.address or ''} {prop.city or ''} {prop.state or ''} {prop.description or ''} {prop.title or ''}"

        # For now, we don't generate embeddings (would require LLM service)
        # In production, you'd call: embedding = llm_service.embed_text(text)
        embedding = None

        hybrid_search.index_property(
            property_id=property_id,
            text=text,
            embedding=embedding
        )

        return {"message": f"Property {property_id} indexed successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def search_health():
    """Check hybrid search engine health."""
    return {
        "status": "healthy" if hybrid_search.conn else "degraded",
        "fts5_enabled": hybrid_search.conn is not None,
        "vector_enabled": hybrid_search._has_embeddings()
    }
