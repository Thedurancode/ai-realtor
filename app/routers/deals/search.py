"""
Search Router — Semantic vector search endpoints.

POST /search/properties   — Semantic property search with optional filters
POST /search/research     — Search across dossiers + evidence
GET  /search/similar/{id} — Find similar properties
POST /search/backfill     — Backfill embeddings for existing data
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.embedding_service import embedding_service
from app.schemas.search import (
    SemanticSearchRequest,
    ResearchSearchRequest,
    PropertySearchResponse,
    ResearchSearchResponse,
    BackfillRequest,
    BackfillResponse,
)

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/properties", response_model=PropertySearchResponse)
def search_properties(req: SemanticSearchRequest, db: Session = Depends(get_db)):
    """
    Semantic search across properties using natural language.

    Example: "Modern condo in Brooklyn under $700k with parking"
    """
    try:
        results = embedding_service.search_properties(
            db,
            query=req.query,
            limit=req.limit,
            status=req.status,
            property_type=req.property_type,
            min_price=req.min_price,
            max_price=req.max_price,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Build voice summary
    count = len(results)
    if count == 0:
        voice = f"No properties found matching '{req.query}'."
    elif count == 1:
        r = results[0]
        voice = f"Found 1 property: {r['address']} at ${r['price']:,.0f}." if r.get("price") else f"Found 1 property: {r['address']}."
    else:
        voice = f"Found {count} properties matching '{req.query}'. "
        top = results[0]
        voice += f"Best match: {top['address']}"
        if top.get("price"):
            voice += f" at ${top['price']:,.0f}"
        voice += f" ({top['similarity']:.0%} match)."

    return PropertySearchResponse(
        results=results,
        query=req.query,
        count=count,
        voice_summary=voice,
    )


@router.post("/research", response_model=ResearchSearchResponse)
def search_research(req: ResearchSearchRequest, db: Session = Depends(get_db)):
    """
    Search across research dossiers and evidence items.

    Example: "flood risk for properties in Miami Beach"
    """
    try:
        data = embedding_service.search_research(
            db,
            query=req.query,
            dossier_limit=req.dossier_limit,
            evidence_limit=req.evidence_limit,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    total = len(data["dossiers"]) + len(data["evidence"])
    if total == 0:
        voice = f"No research found matching '{req.query}'."
    else:
        voice = f"Found {len(data['dossiers'])} dossiers and {len(data['evidence'])} evidence items matching '{req.query}'."

    return ResearchSearchResponse(
        dossiers=data["dossiers"],
        evidence=data["evidence"],
        query=req.query,
        total_count=total,
        voice_summary=voice,
    )


@router.get("/similar/{property_id}")
def find_similar_properties(
    property_id: int,
    limit: int = 5,
    db: Session = Depends(get_db),
):
    """Find properties similar to a given property using vector similarity."""
    try:
        results = embedding_service.find_similar_properties(db, property_id, limit)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    count = len(results)
    if count == 0:
        voice = f"No similar properties found for property {property_id}. It may not have an embedding yet — try running a backfill."
    else:
        voice = f"Found {count} properties similar to property {property_id}. "
        top = results[0]
        voice += f"Most similar: {top['address']}"
        if top.get("price"):
            voice += f" at ${top['price']:,.0f}"
        voice += f" ({top['similarity']:.0%} match)."

    return {
        "property_id": property_id,
        "similar": results,
        "count": count,
        "voice_summary": voice,
    }


@router.post("/backfill", response_model=BackfillResponse)
def backfill_embeddings(req: BackfillRequest, db: Session = Depends(get_db)):
    """
    Backfill embeddings for existing data that doesn't have them yet.

    table: "properties" | "property_recaps" | "dossiers" | "evidence" | "all"
    """
    try:
        result = embedding_service.backfill(db, req.table)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result
