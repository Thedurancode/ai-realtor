from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.property_media import PropertyMedia
from app.schemas.property_media import (
    MediaCreate,
    MediaListResponse,
    MediaReorderRequest,
    MediaResponse,
    MediaUpdate,
)

router = APIRouter(prefix="/media", tags=["property-media"])


@router.post("/", response_model=MediaResponse, status_code=201)
def create_media(payload: MediaCreate, db: Session = Depends(get_db)):
    media = PropertyMedia(**payload.model_dump())
    db.add(media)
    db.commit()
    db.refresh(media)
    return MediaResponse.model_validate(media)


@router.get("/property/{property_id}", response_model=MediaListResponse)
def list_property_media(
    property_id: int,
    media_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    q = db.query(PropertyMedia).filter(PropertyMedia.property_id == property_id)
    if media_type:
        q = q.filter(PropertyMedia.media_type == media_type)
    q = q.order_by(PropertyMedia.sort_order.asc())
    items = q.all()
    return MediaListResponse(
        property_id=property_id,
        media=[MediaResponse.model_validate(m) for m in items],
        total=len(items),
    )


@router.get("/{media_id}", response_model=MediaResponse)
def get_media(media_id: int, db: Session = Depends(get_db)):
    media = db.query(PropertyMedia).filter(PropertyMedia.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    return MediaResponse.model_validate(media)


@router.patch("/{media_id}", response_model=MediaResponse)
def update_media(media_id: int, payload: MediaUpdate, db: Session = Depends(get_db)):
    media = db.query(PropertyMedia).filter(PropertyMedia.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(media, key, value)
    db.commit()
    db.refresh(media)
    return MediaResponse.model_validate(media)


@router.delete("/{media_id}", status_code=204)
def delete_media(media_id: int, db: Session = Depends(get_db)):
    media = db.query(PropertyMedia).filter(PropertyMedia.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    db.delete(media)
    db.commit()


@router.post("/property/{property_id}/reorder", response_model=MediaListResponse)
def reorder_media(property_id: int, payload: MediaReorderRequest, db: Session = Depends(get_db)):
    for item in payload.items:
        media = db.query(PropertyMedia).filter(
            PropertyMedia.id == item.media_id,
            PropertyMedia.property_id == property_id,
        ).first()
        if media:
            media.sort_order = item.sort_order
    db.commit()

    items = (
        db.query(PropertyMedia)
        .filter(PropertyMedia.property_id == property_id)
        .order_by(PropertyMedia.sort_order.asc())
        .all()
    )
    return MediaListResponse(
        property_id=property_id,
        media=[MediaResponse.model_validate(m) for m in items],
        total=len(items),
    )
