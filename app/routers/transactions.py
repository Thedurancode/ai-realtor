from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.transaction import MilestoneStatus, Transaction, TransactionMilestone, TransactionStatus
from app.schemas.transaction import (
    MilestoneCreate,
    MilestoneResponse,
    MilestoneUpdate,
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/", response_model=TransactionResponse, status_code=201)
def create_transaction(payload: TransactionCreate, request: Request, db: Session = Depends(get_db)):
    agent_id = getattr(request.state, "agent_id", 1)
    txn = Transaction(agent_id=agent_id, **payload.model_dump())
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return TransactionResponse.model_validate(txn)


@router.get("/", response_model=list[TransactionResponse])
def list_transactions(
    request: Request,
    status: str | None = Query(default=None),
    property_id: int | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    db: Session = Depends(get_db),
):
    agent_id = getattr(request.state, "agent_id", 1)
    q = db.query(Transaction).options(joinedload(Transaction.milestones)).filter(Transaction.agent_id == agent_id)
    if status:
        q = q.filter(Transaction.status == status)
    if property_id:
        q = q.filter(Transaction.property_id == property_id)
    q = q.order_by(Transaction.created_at.desc())
    txns = q.offset(offset).limit(limit).all()
    return [TransactionResponse.model_validate(t) for t in txns]


@router.get("/closing-soon", response_model=list[TransactionResponse])
def closing_soon(
    request: Request,
    days: int = Query(default=14),
    db: Session = Depends(get_db),
):
    agent_id = getattr(request.state, "agent_id", 1)
    cutoff = datetime.now(timezone.utc) + timedelta(days=days)
    txns = (
        db.query(Transaction)
        .options(joinedload(Transaction.milestones))
        .filter(
            Transaction.agent_id == agent_id,
            Transaction.closing_date <= cutoff,
            Transaction.status.notin_([TransactionStatus.CLOSED, TransactionStatus.FELL_THROUGH]),
        )
        .order_by(Transaction.closing_date.asc())
        .all()
    )
    return [TransactionResponse.model_validate(t) for t in txns]


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    txn = (
        db.query(Transaction)
        .options(joinedload(Transaction.milestones))
        .filter(Transaction.id == transaction_id)
        .first()
    )
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return TransactionResponse.model_validate(txn)


@router.patch("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(transaction_id: int, payload: TransactionUpdate, db: Session = Depends(get_db)):
    txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(txn, key, value)
    db.commit()
    db.refresh(txn)
    return TransactionResponse.model_validate(txn)


@router.post("/{transaction_id}/milestones", response_model=MilestoneResponse, status_code=201)
def add_milestone(transaction_id: int, payload: MilestoneCreate, db: Session = Depends(get_db)):
    txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    milestone = TransactionMilestone(transaction_id=transaction_id, **payload.model_dump())
    db.add(milestone)
    db.commit()
    db.refresh(milestone)
    return MilestoneResponse.model_validate(milestone)


@router.patch("/{transaction_id}/milestones/{milestone_id}", response_model=MilestoneResponse)
def update_milestone(transaction_id: int, milestone_id: int, payload: MilestoneUpdate, db: Session = Depends(get_db)):
    milestone = (
        db.query(TransactionMilestone)
        .filter(TransactionMilestone.id == milestone_id, TransactionMilestone.transaction_id == transaction_id)
        .first()
    )
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        if key == "status" and value == MilestoneStatus.COMPLETED.value:
            milestone.completed_at = datetime.now(timezone.utc)
        setattr(milestone, key, value)
    db.commit()
    db.refresh(milestone)
    return MilestoneResponse.model_validate(milestone)


@router.get("/{transaction_id}/timeline", response_model=list[MilestoneResponse])
def get_timeline(transaction_id: int, db: Session = Depends(get_db)):
    milestones = (
        db.query(TransactionMilestone)
        .filter(TransactionMilestone.transaction_id == transaction_id)
        .order_by(TransactionMilestone.sort_order.asc())
        .all()
    )
    return [MilestoneResponse.model_validate(m) for m in milestones]
