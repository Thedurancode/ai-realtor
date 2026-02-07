from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.offer import (
    CounterOfferCreate,
    MAOResponse,
    OfferCreate,
    OfferResponse,
    OfferSummary,
)
from app.services import offer_service

router = APIRouter(prefix="/offers", tags=["offers"])


@router.post("/", response_model=OfferResponse, status_code=201)
def create_offer(payload: OfferCreate, db: Session = Depends(get_db)):
    try:
        offer = offer_service.create_offer(db=db, payload=payload)
        return OfferResponse.model_validate(offer)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[OfferResponse])
def list_offers(
    property_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    offers = offer_service.list_offers(db=db, property_id=property_id, status=status)
    return [OfferResponse.model_validate(o) for o in offers]


@router.get("/{offer_id}", response_model=OfferResponse)
def get_offer(offer_id: int, db: Session = Depends(get_db)):
    offer = offer_service.get_offer(db=db, offer_id=offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    return OfferResponse.model_validate(offer)


@router.post("/{offer_id}/counter", response_model=OfferResponse, status_code=201)
def counter_offer(offer_id: int, payload: CounterOfferCreate, db: Session = Depends(get_db)):
    try:
        offer = offer_service.counter_offer(db=db, offer_id=offer_id, payload=payload)
        return OfferResponse.model_validate(offer)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{offer_id}/accept", response_model=OfferResponse)
def accept_offer(offer_id: int, db: Session = Depends(get_db)):
    try:
        offer = offer_service.accept_offer(db=db, offer_id=offer_id)
        return OfferResponse.model_validate(offer)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{offer_id}/reject", response_model=OfferResponse)
def reject_offer(offer_id: int, db: Session = Depends(get_db)):
    try:
        offer = offer_service.reject_offer(db=db, offer_id=offer_id)
        return OfferResponse.model_validate(offer)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{offer_id}/withdraw", response_model=OfferResponse)
def withdraw_offer(offer_id: int, db: Session = Depends(get_db)):
    try:
        offer = offer_service.withdraw_offer(db=db, offer_id=offer_id)
        return OfferResponse.model_validate(offer)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{offer_id}/chain", response_model=list[OfferResponse])
def get_negotiation_chain(offer_id: int, db: Session = Depends(get_db)):
    chain = offer_service.get_negotiation_chain(db=db, offer_id=offer_id)
    if not chain:
        raise HTTPException(status_code=404, detail="Offer not found")
    return [OfferResponse.model_validate(o) for o in chain]


@router.get("/property/{property_id}/summary", response_model=OfferSummary)
def get_property_offer_summary(property_id: int, db: Session = Depends(get_db)):
    try:
        return offer_service.get_offer_summary(db=db, property_id=property_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/property/{property_id}/mao", response_model=MAOResponse)
def calculate_mao(property_id: int, db: Session = Depends(get_db)):
    try:
        return offer_service.calculate_mao(db=db, property_id=property_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
