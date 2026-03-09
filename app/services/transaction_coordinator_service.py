"""Transaction Coordinator Service — shepherds deals from accepted offer to closing.

Auto-creates milestones, tracks deadlines, flags overdue items, and logs everything
to the deal journal for audit trail.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.transaction import (
    Transaction, TransactionMilestone,
    TransactionStatus, MilestoneStatus, PartyRole,
)

logger = logging.getLogger(__name__)

# Default milestone templates — auto-created when a transaction starts
DEFAULT_MILESTONES = [
    {"name": "Attorney Review", "role": PartyRole.ATTORNEY, "days_from_accept": 3},
    {"name": "Home Inspection", "role": PartyRole.INSPECTOR, "days_from_accept": 10},
    {"name": "Inspection Resolution", "role": PartyRole.BUYER_AGENT, "days_from_accept": 14},
    {"name": "Appraisal Ordered", "role": PartyRole.LENDER, "days_from_accept": 7},
    {"name": "Appraisal Completed", "role": PartyRole.APPRAISER, "days_from_accept": 21},
    {"name": "Mortgage Commitment", "role": PartyRole.LENDER, "days_from_accept": 30},
    {"name": "Title Search Clear", "role": PartyRole.TITLE_COMPANY, "days_from_accept": 21},
    {"name": "Final Walkthrough", "role": PartyRole.BUYER, "days_from_accept": -1},  # -1 = 1 day before closing
    {"name": "Closing", "role": PartyRole.TITLE_COMPANY, "days_from_accept": None},  # uses closing_date
]


class TransactionCoordinatorService:

    # ── Create ──────────────────────────────────────────────

    def create_transaction(
        self,
        db: Session,
        property_id: int,
        offer_id: int = None,
        title: str = None,
        accepted_date: datetime = None,
        closing_date: datetime = None,
        sale_price: float = None,
        earnest_money: float = None,
        commission_rate: float = None,
        financing_type: str = None,
        parties: list = None,
        notes: str = None,
        attorney_review_deadline: datetime = None,
        inspection_deadline: datetime = None,
        appraisal_deadline: datetime = None,
        mortgage_contingency_date: datetime = None,
    ) -> Transaction:
        """Create a new transaction and auto-generate milestone timeline."""

        accepted = accepted_date or datetime.now(timezone.utc)
        close = closing_date or (accepted + timedelta(days=45))

        txn = Transaction(
            property_id=property_id,
            offer_id=offer_id,
            title=title or f"Transaction — Property #{property_id}",
            status=TransactionStatus.INITIATED,
            accepted_date=accepted,
            closing_date=close,
            sale_price=sale_price,
            earnest_money=earnest_money,
            commission_rate=commission_rate,
            financing_type=financing_type,
            parties=[p.model_dump() if hasattr(p, 'model_dump') else p for p in (parties or [])],
            notes=notes,
            attorney_review_deadline=attorney_review_deadline or (accepted + timedelta(days=3)),
            inspection_deadline=inspection_deadline or (accepted + timedelta(days=10)),
            appraisal_deadline=appraisal_deadline or (accepted + timedelta(days=21)),
            mortgage_contingency_date=mortgage_contingency_date or (accepted + timedelta(days=30)),
        )
        db.add(txn)
        db.flush()

        # Auto-create milestones
        self._create_default_milestones(db, txn)

        db.commit()
        db.refresh(txn)

        # Log to deal journal
        self._log_journal_safe(db, txn, "Transaction initiated", f"Transaction created for property #{property_id}. Closing target: {close.strftime('%Y-%m-%d')}.")

        logger.info(f"Transaction #{txn.id} created for property #{property_id}")
        return txn

    def _create_default_milestones(self, db: Session, txn: Transaction):
        """Generate milestone timeline based on accepted date and closing date."""
        accepted = txn.accepted_date
        closing = txn.closing_date

        for tmpl in DEFAULT_MILESTONES:
            if tmpl["days_from_accept"] is None:
                due = closing
            elif tmpl["days_from_accept"] < 0:
                due = closing + timedelta(days=tmpl["days_from_accept"])
            else:
                due = accepted + timedelta(days=tmpl["days_from_accept"])

            milestone = TransactionMilestone(
                transaction_id=txn.id,
                name=tmpl["name"],
                status=MilestoneStatus.PENDING,
                assigned_role=tmpl["role"],
                due_date=due,
            )
            db.add(milestone)

    # ── Read ────────────────────────────────────────────────

    def get_transaction(self, db: Session, txn_id: int) -> Optional[Transaction]:
        return db.query(Transaction).filter(Transaction.id == txn_id).first()

    def list_transactions(
        self,
        db: Session,
        status: str = None,
        property_id: int = None,
        limit: int = 50,
    ) -> List[Transaction]:
        q = db.query(Transaction).order_by(Transaction.closing_date.asc())
        if status:
            q = q.filter(Transaction.status == TransactionStatus(status))
        if property_id:
            q = q.filter(Transaction.property_id == property_id)
        return q.limit(limit).all()

    def get_active_transactions(self, db: Session) -> List[Transaction]:
        """Get all non-terminal transactions."""
        terminal = {TransactionStatus.CLOSED, TransactionStatus.FELL_THROUGH, TransactionStatus.CANCELLED}
        return db.query(Transaction).filter(
            Transaction.status.notin_(terminal)
        ).order_by(Transaction.closing_date.asc()).all()

    def get_transaction_summary(self, db: Session, txn_id: int) -> Optional[Dict]:
        """Summary with milestone progress and risk flags."""
        txn = self.get_transaction(db, txn_id)
        if not txn:
            return None

        milestones = txn.milestones
        completed = sum(1 for m in milestones if m.status == MilestoneStatus.COMPLETED)
        overdue = sum(1 for m in milestones if m.status == MilestoneStatus.OVERDUE)
        now = datetime.now(timezone.utc)
        if txn.closing_date:
            closing = txn.closing_date if txn.closing_date.tzinfo else txn.closing_date.replace(tzinfo=timezone.utc)
            days_to_close = (closing - now).days
        else:
            days_to_close = None

        return {
            "id": txn.id,
            "property_id": txn.property_id,
            "status": txn.status.value,
            "title": txn.title,
            "closing_date": txn.closing_date.isoformat() if txn.closing_date else None,
            "sale_price": txn.sale_price,
            "days_to_close": days_to_close,
            "milestones_completed": completed,
            "milestones_total": len(milestones),
            "overdue_milestones": overdue,
            "risk_flags": txn.risk_flags or [],
        }

    # ── Update ──────────────────────────────────────────────

    def update_milestone(
        self,
        db: Session,
        milestone_id: int,
        status: str = None,
        outcome_notes: str = None,
        completed_at: datetime = None,
        due_date: datetime = None,
        assigned_name: str = None,
        assigned_contact: str = None,
    ) -> Optional[TransactionMilestone]:
        """Update a milestone and auto-advance transaction status."""
        milestone = db.query(TransactionMilestone).filter(TransactionMilestone.id == milestone_id).first()
        if not milestone:
            return None

        if status:
            milestone.status = MilestoneStatus(status)
            milestone.reminder_sent = False  # Reset so new status gets fresh reminders
            if status == "completed" and not milestone.completed_at:
                milestone.completed_at = completed_at or datetime.now(timezone.utc)
        if outcome_notes:
            milestone.outcome_notes = outcome_notes
        if due_date:
            milestone.due_date = due_date
        if assigned_name:
            milestone.assigned_name = assigned_name
        if assigned_contact:
            milestone.assigned_contact = assigned_contact

        db.flush()

        # Auto-advance transaction status based on completed milestones
        txn = milestone.transaction
        self._auto_advance_status(db, txn)

        db.commit()
        db.refresh(milestone)

        # Journal the update (best-effort, after commit so main op is safe)
        self._log_journal_safe(
            db, txn,
            f"Milestone updated: {milestone.name}",
            f"{milestone.name} - {milestone.status.value}. {outcome_notes or ''}",
        )

        return milestone

    def advance_status(self, db: Session, txn_id: int, new_status: str, notes: str = None) -> Optional[Transaction]:
        """Manually advance transaction to a new status."""
        txn = self.get_transaction(db, txn_id)
        if not txn:
            return None

        old_status = txn.status.value
        txn.status = TransactionStatus(new_status)

        if new_status == "closed":
            txn.closed_at = datetime.now(timezone.utc)

        if notes:
            txn.notes = f"{txn.notes}\n\n[{datetime.now(timezone.utc).strftime('%Y-%m-%d')}] {notes}" if txn.notes else notes

        db.commit()
        db.refresh(txn)

        self._log_journal_safe(db, txn, f"Status: {old_status} → {new_status}", notes or "")
        return txn

    def add_party(self, db: Session, txn_id: int, name: str, role: str, email: str = None, phone: str = None) -> Optional[Transaction]:
        txn = self.get_transaction(db, txn_id)
        if not txn:
            return None

        parties = list(txn.parties or [])
        parties.append({"name": name, "role": role, "email": email, "phone": phone})
        txn.parties = parties

        db.commit()
        db.refresh(txn)
        return txn

    def add_risk_flag(self, db: Session, txn_id: int, flag: str) -> Optional[Transaction]:
        txn = self.get_transaction(db, txn_id)
        if not txn:
            return None

        flags = list(txn.risk_flags or [])
        if flag not in flags:
            flags.append(flag)
            txn.risk_flags = flags
            db.commit()
            db.refresh(txn)
            self._log_journal_safe(db, txn, f"Risk flag added: {flag}", "")
        return txn

    # ── Deadline Checker (called by cron) ───────────────────

    def check_deadlines(self, db: Session) -> List[Dict]:
        """Scan all active transactions for overdue/upcoming milestones. Returns alerts.

        Uses reminder_sent flag to avoid duplicate notifications — once a milestone
        is flagged, it won't generate another alert until its status changes.
        """
        alerts = []
        now = datetime.now(timezone.utc)
        tomorrow = now + timedelta(days=1)

        active_txns = self.get_active_transactions(db)
        for txn in active_txns:
            for m in txn.milestones:
                if m.status in (MilestoneStatus.COMPLETED, MilestoneStatus.WAIVED, MilestoneStatus.FAILED):
                    continue
                if not m.due_date:
                    continue

                due = m.due_date if m.due_date.tzinfo else m.due_date.replace(tzinfo=timezone.utc)
                if due < now and m.status != MilestoneStatus.OVERDUE:
                    # First time going overdue — always alert
                    m.status = MilestoneStatus.OVERDUE
                    m.reminder_sent = True
                    alerts.append({
                        "type": "overdue",
                        "transaction_id": txn.id,
                        "property_id": txn.property_id,
                        "milestone": m.name,
                        "milestone_id": m.id,
                        "due_date": m.due_date.isoformat(),
                        "assigned_role": m.assigned_role.value if m.assigned_role else None,
                        "message": f"OVERDUE: {m.name} for {txn.title} was due {m.due_date.strftime('%m/%d')}",
                    })
                elif due <= tomorrow and m.status == MilestoneStatus.PENDING and not m.reminder_sent:
                    # Upcoming — only alert once per milestone
                    m.reminder_sent = True
                    alerts.append({
                        "type": "upcoming",
                        "transaction_id": txn.id,
                        "property_id": txn.property_id,
                        "milestone": m.name,
                        "milestone_id": m.id,
                        "due_date": m.due_date.isoformat(),
                        "assigned_role": m.assigned_role.value if m.assigned_role else None,
                        "message": f"DUE SOON: {m.name} for {txn.title} due {m.due_date.strftime('%m/%d')}",
                    })

        if alerts:
            db.commit()
        return alerts

    # ── Pipeline Dashboard ──────────────────────────────────

    def get_pipeline(self, db: Session) -> Dict:
        """Transaction pipeline overview — counts by status + upcoming deadlines."""
        active = self.get_active_transactions(db)
        now = datetime.now(timezone.utc)

        by_status = {}
        upcoming = []
        total_value = 0.0

        for txn in active:
            status = txn.status.value
            by_status[status] = by_status.get(status, 0) + 1
            if txn.sale_price:
                total_value += txn.sale_price

            for m in txn.milestones:
                if m.status in (MilestoneStatus.COMPLETED, MilestoneStatus.WAIVED, MilestoneStatus.FAILED):
                    continue
                due = m.due_date.replace(tzinfo=timezone.utc) if m.due_date and not m.due_date.tzinfo else m.due_date
                if due and due <= now + timedelta(days=7):
                    upcoming.append({
                        "transaction_id": txn.id,
                        "title": txn.title,
                        "milestone": m.name,
                        "due_date": m.due_date.isoformat(),
                        "status": m.status.value,
                    })

        upcoming.sort(key=lambda x: x["due_date"])

        return {
            "active_count": len(active),
            "total_pipeline_value": total_value,
            "by_status": by_status,
            "upcoming_7_days": upcoming[:20],
        }

    # ── Internal Helpers ────────────────────────────────────

    def _auto_advance_status(self, db: Session, txn: Transaction):
        """Move transaction status forward based on completed milestones."""
        completed_names = {m.name for m in txn.milestones if m.status == MilestoneStatus.COMPLETED}

        status_map = [
            ({"Attorney Review"}, TransactionStatus.ATTORNEY_REVIEW),
            ({"Home Inspection", "Inspection Resolution"}, TransactionStatus.INSPECTIONS),
            ({"Appraisal Completed"}, TransactionStatus.APPRAISAL),
            ({"Mortgage Commitment"}, TransactionStatus.MORTGAGE_CONTINGENCY),
            ({"Title Search Clear"}, TransactionStatus.TITLE_SEARCH),
            ({"Final Walkthrough"}, TransactionStatus.FINAL_WALKTHROUGH),
            ({"Closing"}, TransactionStatus.CLOSED),
        ]

        # Walk forward — last matching set wins
        new_status = txn.status
        for required, status in status_map:
            if required.issubset(completed_names):
                new_status = status

        if new_status != txn.status:
            txn.status = new_status
            if new_status == TransactionStatus.CLOSED:
                txn.closed_at = datetime.now(timezone.utc)

    def _log_journal_safe(self, db: Session, txn: Transaction, title: str, content: str):
        """Log transaction event to deal journal (best-effort, never breaks caller).

        Uses a separate session so journal failures can't corrupt the main transaction.
        """
        try:
            from app.database import SessionLocal
            from app.services.deal_journal_service import deal_journal_service
            from app.models.deal_journal import JournalEntryType
            journal_db = SessionLocal()
            try:
                deal_journal_service.log_entry(
                    journal_db,
                    entry_type=JournalEntryType.NOTE,
                    title=f"[TC] {title}",
                    content=content,
                    property_id=txn.property_id,
                    tags=f"transaction,txn-{txn.id}",
                )
            finally:
                journal_db.close()
        except Exception as e:
            logger.warning(f"Failed to log journal entry: {e}")


transaction_coordinator = TransactionCoordinatorService()
