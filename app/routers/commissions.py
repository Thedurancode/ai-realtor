from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.commission import Commission, CommissionStatus
from app.schemas.commission import (
    CommissionCreate,
    CommissionResponse,
    CommissionSummaryResponse,
    CommissionUpdate,
)

router = APIRouter(prefix="/commissions", tags=["commissions"])


def _calc_net(commission: Commission):
    """Recalculate net amount based on commission and split."""
    if commission.commission_amount and commission.split_percentage:
        commission.net_amount = round(commission.commission_amount * commission.split_percentage / 100, 2)
    elif commission.sale_price and commission.commission_rate and commission.split_percentage:
        gross = commission.sale_price * commission.commission_rate / 100
        commission.net_amount = round(gross * commission.split_percentage / 100, 2)
        commission.commission_amount = round(gross, 2)


@router.post("/", response_model=CommissionResponse, status_code=201)
def create_commission(payload: CommissionCreate, request: Request, db: Session = Depends(get_db)):
    agent_id = getattr(request.state, "agent_id", 1)
    commission = Commission(agent_id=agent_id, **payload.model_dump())
    _calc_net(commission)
    db.add(commission)
    db.commit()
    db.refresh(commission)
    return CommissionResponse.model_validate(commission)


@router.get("/", response_model=list[CommissionResponse])
def list_commissions(
    request: Request,
    status: str | None = Query(default=None),
    property_id: int | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    db: Session = Depends(get_db),
):
    agent_id = getattr(request.state, "agent_id", 1)
    q = db.query(Commission).filter(Commission.agent_id == agent_id)
    if status:
        q = q.filter(Commission.status == status)
    if property_id:
        q = q.filter(Commission.property_id == property_id)
    q = q.order_by(Commission.created_at.desc())
    commissions = q.offset(offset).limit(limit).all()
    return [CommissionResponse.model_validate(c) for c in commissions]


@router.get("/summary", response_model=CommissionSummaryResponse)
def commission_summary(request: Request, db: Session = Depends(get_db)):
    agent_id = getattr(request.state, "agent_id", 1)
    commissions = db.query(Commission).filter(Commission.agent_id == agent_id).all()

    earned = sum(c.net_amount or 0 for c in commissions if c.status == CommissionStatus.PAID)
    pending = sum(c.net_amount or 0 for c in commissions if c.status in (CommissionStatus.PENDING, CommissionStatus.INVOICED))
    projected = sum(c.net_amount or 0 for c in commissions if c.status == CommissionStatus.PROJECTED)

    return CommissionSummaryResponse(
        total_earned=earned,
        total_pending=pending,
        total_projected=projected,
        count_paid=sum(1 for c in commissions if c.status == CommissionStatus.PAID),
        count_pending=sum(1 for c in commissions if c.status in (CommissionStatus.PENDING, CommissionStatus.INVOICED)),
        count_projected=sum(1 for c in commissions if c.status == CommissionStatus.PROJECTED),
    )


@router.get("/property/{property_id}", response_model=CommissionResponse)
def get_property_commission(property_id: int, request: Request, db: Session = Depends(get_db)):
    agent_id = getattr(request.state, "agent_id", 1)
    commission = (
        db.query(Commission)
        .filter(Commission.agent_id == agent_id, Commission.property_id == property_id)
        .first()
    )
    if not commission:
        raise HTTPException(status_code=404, detail="Commission not found for this property")
    return CommissionResponse.model_validate(commission)


@router.patch("/{commission_id}", response_model=CommissionResponse)
def update_commission(commission_id: int, payload: CommissionUpdate, db: Session = Depends(get_db)):
    commission = db.query(Commission).filter(Commission.id == commission_id).first()
    if not commission:
        raise HTTPException(status_code=404, detail="Commission not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(commission, key, value)
    _calc_net(commission)
    db.commit()
    db.refresh(commission)
    return CommissionResponse.model_validate(commission)
