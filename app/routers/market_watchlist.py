"""Market Watchlist router — CRUD + toggle + manual check."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.watchlist_service import watchlist_service

router = APIRouter(prefix="/watchlists", tags=["watchlists"])


# ── Schemas ──────────────────────────────────────────────────────────

class WatchlistCreate(BaseModel):
    agent_id: int
    name: str = Field(..., max_length=255)
    description: str | None = None
    criteria: dict = Field(
        ...,
        description="Search criteria: {city, state, property_type, min_price, max_price, min_bedrooms, min_bathrooms, min_sqft}",
    )


class WatchlistUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    criteria: dict | None = None


class WatchlistResponse(BaseModel):
    id: int
    agent_id: int
    name: str
    description: str | None
    criteria: dict
    is_active: bool
    match_count: int
    last_matched_at: str | None
    created_at: str | None
    updated_at: str | None

    model_config = {"from_attributes": True}


# ── Endpoints ────────────────────────────────────────────────────────

@router.post("/", status_code=201)
def create_watchlist(body: WatchlistCreate, db: Session = Depends(get_db)):
    wl = watchlist_service.create(
        db,
        agent_id=body.agent_id,
        name=body.name,
        criteria=body.criteria,
        description=body.description,
    )
    return _serialize(wl)


@router.get("/")
def list_watchlists(
    agent_id: int | None = None,
    is_active: bool | None = None,
    db: Session = Depends(get_db),
):
    items = watchlist_service.list(db, agent_id=agent_id, is_active=is_active)
    return [_serialize(w) for w in items]


@router.get("/{watchlist_id}")
def get_watchlist(watchlist_id: int, db: Session = Depends(get_db)):
    wl = watchlist_service.get(db, watchlist_id)
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return _serialize(wl)


@router.put("/{watchlist_id}")
def update_watchlist(watchlist_id: int, body: WatchlistUpdate, db: Session = Depends(get_db)):
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    wl = watchlist_service.update(db, watchlist_id, **updates)
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return _serialize(wl)


@router.delete("/{watchlist_id}", status_code=204)
def delete_watchlist(watchlist_id: int, db: Session = Depends(get_db)):
    ok = watchlist_service.delete(db, watchlist_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return None


@router.post("/{watchlist_id}/toggle")
def toggle_watchlist(watchlist_id: int, db: Session = Depends(get_db)):
    wl = watchlist_service.toggle(db, watchlist_id)
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return _serialize(wl)


@router.post("/check/{property_id}")
def check_property_against_watchlists(property_id: int, db: Session = Depends(get_db)):
    result = watchlist_service.check_property(db, property_id)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ── Helpers ──────────────────────────────────────────────────────────

def _serialize(wl) -> dict:
    return {
        "id": wl.id,
        "agent_id": wl.agent_id,
        "name": wl.name,
        "description": wl.description,
        "criteria": wl.criteria,
        "is_active": wl.is_active,
        "match_count": wl.match_count or 0,
        "last_matched_at": wl.last_matched_at.isoformat() if wl.last_matched_at else None,
        "created_at": wl.created_at.isoformat() if wl.created_at else None,
        "updated_at": wl.updated_at.isoformat() if wl.updated_at else None,
    }
