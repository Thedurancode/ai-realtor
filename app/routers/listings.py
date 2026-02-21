from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.listing import Listing, ListingPriceChange, ListingStatus
from app.schemas.listing import (
    ListingCreate,
    ListingResponse,
    ListingUpdate,
)

router = APIRouter(prefix="/listings", tags=["listings"])


@router.post("/", response_model=ListingResponse, status_code=201)
def create_listing(payload: ListingCreate, request: Request, db: Session = Depends(get_db)):
    agent_id = getattr(request.state, "agent_id", 1)
    listing = Listing(
        agent_id=agent_id,
        original_price=payload.list_price,
        **payload.model_dump(),
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return ListingResponse.model_validate(listing)


@router.get("/active", response_model=list[ListingResponse])
def list_active(
    request: Request,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    db: Session = Depends(get_db),
):
    agent_id = getattr(request.state, "agent_id", 1)
    listings = (
        db.query(Listing)
        .options(joinedload(Listing.price_history))
        .filter(Listing.agent_id == agent_id, Listing.status == ListingStatus.ACTIVE)
        .order_by(Listing.published_at.desc().nullslast())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [ListingResponse.model_validate(l) for l in listings]


@router.get("/{listing_id}", response_model=ListingResponse)
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = (
        db.query(Listing)
        .options(joinedload(Listing.price_history))
        .filter(Listing.id == listing_id)
        .first()
    )
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return ListingResponse.model_validate(listing)


@router.post("/{listing_id}/publish", response_model=ListingResponse)
def publish_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    listing.status = ListingStatus.ACTIVE
    listing.published_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(listing)
    return ListingResponse.model_validate(listing)


@router.post("/{listing_id}/unpublish", response_model=ListingResponse)
def unpublish_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    listing.status = ListingStatus.WITHDRAWN
    db.commit()
    db.refresh(listing)
    return ListingResponse.model_validate(listing)


@router.patch("/{listing_id}", response_model=ListingResponse)
def update_listing(listing_id: int, payload: ListingUpdate, request: Request, db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Track price changes
    if payload.list_price and payload.list_price != listing.list_price:
        change = ListingPriceChange(
            listing_id=listing_id,
            old_price=listing.list_price,
            new_price=payload.list_price,
        )
        db.add(change)

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(listing, key, value)
    db.commit()
    db.refresh(listing)
    return ListingResponse.model_validate(listing)


@router.get("/{listing_id}/history", response_model=list)
def get_price_history(listing_id: int, db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    changes = (
        db.query(ListingPriceChange)
        .filter(ListingPriceChange.listing_id == listing_id)
        .order_by(ListingPriceChange.changed_at.desc())
        .all()
    )
    return [
        {
            "id": c.id,
            "old_price": c.old_price,
            "new_price": c.new_price,
            "reason": c.reason,
            "changed_at": str(c.changed_at),
        }
        for c in changes
    ]
