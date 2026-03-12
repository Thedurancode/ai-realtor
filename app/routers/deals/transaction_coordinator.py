"""Transaction Coordinator router — manage deal milestones from offer to closing."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app.schemas.transaction import (
    TransactionCreate, TransactionResponse, TransactionSummary,
    MilestoneCreate, MilestoneUpdate, MilestoneResponse,
)
from app.services.transaction_coordinator_service import transaction_coordinator

router = APIRouter(prefix="/transactions", tags=["Transaction Coordinator"])


# ── Transactions ────────────────────────────────────────

@router.post("/", response_model=TransactionResponse)
def create_transaction(payload: TransactionCreate, db: Session = Depends(get_db)):
    txn = transaction_coordinator.create_transaction(
        db=db,
        property_id=payload.property_id,
        offer_id=payload.offer_id,
        title=payload.title,
        accepted_date=payload.accepted_date,
        closing_date=payload.closing_date,
        sale_price=payload.sale_price,
        earnest_money=payload.earnest_money,
        commission_rate=payload.commission_rate,
        financing_type=payload.financing_type,
        parties=payload.parties,
        notes=payload.notes,
        attorney_review_deadline=payload.attorney_review_deadline,
        inspection_deadline=payload.inspection_deadline,
        appraisal_deadline=payload.appraisal_deadline,
        mortgage_contingency_date=payload.mortgage_contingency_date,
    )
    return txn


@router.get("/", response_model=List[TransactionResponse])
def list_transactions(
    status: Optional[str] = Query(None, description="Filter: initiated, attorney_review, inspections, appraisal, mortgage_contingency, title_search, final_walkthrough, closing_scheduled, closed, fell_through, cancelled"),
    property_id: Optional[int] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    return transaction_coordinator.list_transactions(db, status=status, property_id=property_id, limit=limit)


@router.get("/active", response_model=List[TransactionResponse])
def list_active_transactions(db: Session = Depends(get_db)):
    return transaction_coordinator.get_active_transactions(db)


@router.get("/pipeline")
def get_pipeline(db: Session = Depends(get_db)):
    return transaction_coordinator.get_pipeline(db)


@router.get("/check-deadlines")
def check_deadlines(db: Session = Depends(get_db)):
    """Scan all active transactions for overdue or upcoming milestones."""
    alerts = transaction_coordinator.check_deadlines(db)
    return {"alerts": alerts, "count": len(alerts)}


@router.post("/check-deadlines/notify")
async def check_deadlines_and_notify(db: Session = Depends(get_db)):
    """Run the full deadline check with notifications — same as the cron handler."""
    from app.services.cron_tasks import transaction_deadline_handler
    result = await transaction_deadline_handler(db, {})
    return result


@router.get("/{txn_id}", response_model=TransactionResponse)
def get_transaction(txn_id: int, db: Session = Depends(get_db)):
    txn = transaction_coordinator.get_transaction(db, txn_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return txn


@router.get("/{txn_id}/summary")
def get_transaction_summary(txn_id: int, db: Session = Depends(get_db)):
    summary = transaction_coordinator.get_transaction_summary(db, txn_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return summary


@router.put("/{txn_id}/status")
def advance_status(txn_id: int, new_status: str, notes: Optional[str] = None, db: Session = Depends(get_db)):
    txn = transaction_coordinator.advance_status(db, txn_id, new_status, notes)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"status": txn.status.value, "message": f"Transaction advanced to {txn.status.value}"}


@router.post("/{txn_id}/party")
def add_party(
    txn_id: int,
    name: str,
    role: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    db: Session = Depends(get_db),
):
    txn = transaction_coordinator.add_party(db, txn_id, name, role, email, phone)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"parties": txn.parties}


@router.post("/{txn_id}/risk-flag")
def add_risk_flag(txn_id: int, flag: str, db: Session = Depends(get_db)):
    txn = transaction_coordinator.add_risk_flag(db, txn_id, flag)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"risk_flags": txn.risk_flags}


# ── Milestones ──────────────────────────────────────────

@router.post("/{txn_id}/milestones", response_model=MilestoneResponse)
def add_milestone(txn_id: int, payload: MilestoneCreate, db: Session = Depends(get_db)):
    from app.models.transaction import TransactionMilestone, MilestoneStatus, PartyRole
    txn = transaction_coordinator.get_transaction(db, txn_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    milestone = TransactionMilestone(
        transaction_id=txn_id,
        name=payload.name,
        description=payload.description,
        assigned_role=PartyRole(payload.assigned_role) if payload.assigned_role else None,
        assigned_name=payload.assigned_name,
        assigned_contact=payload.assigned_contact,
        due_date=payload.due_date,
        status=MilestoneStatus.PENDING,
    )
    db.add(milestone)
    db.commit()
    db.refresh(milestone)
    return milestone


@router.put("/milestones/{milestone_id}", response_model=MilestoneResponse)
def update_milestone(milestone_id: int, payload: MilestoneUpdate, db: Session = Depends(get_db)):
    milestone = transaction_coordinator.update_milestone(
        db=db,
        milestone_id=milestone_id,
        status=payload.status,
        outcome_notes=payload.outcome_notes,
        completed_at=payload.completed_at,
        due_date=payload.due_date,
        assigned_name=payload.assigned_name,
        assigned_contact=payload.assigned_contact,
    )
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    return milestone
