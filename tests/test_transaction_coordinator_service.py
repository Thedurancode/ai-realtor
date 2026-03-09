"""Tests for TransactionCoordinatorService — unit-level tests with real SQLite DB.

Covers:
- Transaction CRUD (create, read, list, filter)
- Auto-milestone generation on create
- Milestone updates + reminder_sent reset
- Auto-status advancement
- Deadline checking (overdue detection, upcoming alerts, dedup via reminder_sent)
- Pipeline dashboard
- Party + risk flag management
"""

import pytest
from datetime import datetime, timedelta, timezone

from app.models.transaction import (
    Transaction, TransactionMilestone,
    TransactionStatus, MilestoneStatus, PartyRole,
)
from app.services.transaction_coordinator_service import (
    TransactionCoordinatorService,
    DEFAULT_MILESTONES,
)


@pytest.fixture()
def svc():
    return TransactionCoordinatorService()


# ── Create ──────────────────────────────────────────────────────


def test_create_transaction_basic(db, svc, sample_property):
    txn = svc.create_transaction(db, property_id=sample_property.id)
    assert txn.id is not None
    assert txn.property_id == sample_property.id
    assert txn.status == TransactionStatus.INITIATED
    assert txn.title == f"Transaction — Property #{sample_property.id}"


def test_create_transaction_with_details(db, svc, sample_property):
    accepted = datetime(2026, 3, 1, tzinfo=timezone.utc)
    closing = datetime(2026, 4, 15, tzinfo=timezone.utc)

    txn = svc.create_transaction(
        db,
        property_id=sample_property.id,
        title="Deal for 123 Main St",
        accepted_date=accepted,
        closing_date=closing,
        sale_price=350000.0,
        earnest_money=5000.0,
        commission_rate=3.0,
        financing_type="conventional",
        notes="First-time buyer",
    )

    assert txn.title == "Deal for 123 Main St"
    assert txn.sale_price == 350000.0
    assert txn.earnest_money == 5000.0
    assert txn.commission_rate == 3.0
    assert txn.financing_type == "conventional"
    assert txn.notes == "First-time buyer"
    # SQLite strips timezone info, so compare date components
    assert txn.accepted_date.date() == accepted.date()
    assert txn.closing_date.date() == closing.date()


def test_create_transaction_auto_milestones(db, svc, sample_property):
    txn = svc.create_transaction(db, property_id=sample_property.id)
    milestones = txn.milestones
    assert len(milestones) == len(DEFAULT_MILESTONES)

    names = {m.name for m in milestones}
    for tmpl in DEFAULT_MILESTONES:
        assert tmpl["name"] in names

    # All should start as PENDING
    for m in milestones:
        assert m.status == MilestoneStatus.PENDING
        assert m.reminder_sent is False


def test_create_transaction_closing_date_defaults_45_days(db, svc, sample_property):
    before = datetime.now(timezone.utc)
    txn = svc.create_transaction(db, property_id=sample_property.id)
    expected_close = txn.accepted_date + timedelta(days=45)
    # Allow 1 second tolerance
    assert abs((txn.closing_date - expected_close).total_seconds()) < 1


def test_create_transaction_with_parties(db, svc, sample_property):
    txn = svc.create_transaction(
        db,
        property_id=sample_property.id,
        parties=[
            {"name": "John Doe", "role": "buyer", "email": "john@example.com", "phone": "555-0100"},
            {"name": "Jane Smith", "role": "seller_agent"},
        ],
    )
    assert len(txn.parties) == 2
    assert txn.parties[0]["name"] == "John Doe"


def test_milestone_due_dates_calculated_correctly(db, svc, sample_property):
    accepted = datetime(2026, 3, 1, tzinfo=timezone.utc)
    closing = datetime(2026, 4, 15, tzinfo=timezone.utc)

    txn = svc.create_transaction(
        db,
        property_id=sample_property.id,
        accepted_date=accepted,
        closing_date=closing,
    )

    milestones_by_name = {m.name: m for m in txn.milestones}

    # Attorney Review = accepted + 3 days
    assert milestones_by_name["Attorney Review"].due_date.date() == (accepted + timedelta(days=3)).date()

    # Home Inspection = accepted + 10 days
    assert milestones_by_name["Home Inspection"].due_date.date() == (accepted + timedelta(days=10)).date()

    # Final Walkthrough = closing - 1 day
    assert milestones_by_name["Final Walkthrough"].due_date.date() == (closing - timedelta(days=1)).date()

    # Closing = closing_date
    assert milestones_by_name["Closing"].due_date.date() == closing.date()


# ── Read ────────────────────────────────────────────────────────


def test_get_transaction(db, svc, sample_property):
    txn = svc.create_transaction(db, property_id=sample_property.id)
    found = svc.get_transaction(db, txn.id)
    assert found is not None
    assert found.id == txn.id


def test_get_transaction_not_found(db, svc):
    assert svc.get_transaction(db, 99999) is None


def test_list_transactions(db, svc, sample_property, second_property):
    svc.create_transaction(db, property_id=sample_property.id)
    svc.create_transaction(db, property_id=second_property.id)
    txns = svc.list_transactions(db)
    assert len(txns) == 2


def test_list_transactions_filter_by_status(db, svc, sample_property, second_property):
    txn1 = svc.create_transaction(db, property_id=sample_property.id)
    txn2 = svc.create_transaction(db, property_id=second_property.id)
    svc.advance_status(db, txn2.id, "closed")

    active = svc.list_transactions(db, status="initiated")
    assert len(active) == 1
    assert active[0].id == txn1.id


def test_list_transactions_filter_by_property(db, svc, sample_property, second_property):
    svc.create_transaction(db, property_id=sample_property.id)
    svc.create_transaction(db, property_id=second_property.id)

    filtered = svc.list_transactions(db, property_id=sample_property.id)
    assert len(filtered) == 1
    assert filtered[0].property_id == sample_property.id


def test_get_active_transactions_excludes_terminal(db, svc, sample_property, second_property):
    svc.create_transaction(db, property_id=sample_property.id)
    txn2 = svc.create_transaction(db, property_id=second_property.id)
    svc.advance_status(db, txn2.id, "closed")

    active = svc.get_active_transactions(db)
    assert len(active) == 1


def test_get_transaction_summary(db, svc, sample_property):
    txn = svc.create_transaction(
        db,
        property_id=sample_property.id,
        sale_price=400000.0,
    )
    summary = svc.get_transaction_summary(db, txn.id)

    assert summary["id"] == txn.id
    assert summary["status"] == "initiated"
    assert summary["sale_price"] == 400000.0
    assert summary["milestones_total"] == len(DEFAULT_MILESTONES)
    assert summary["milestones_completed"] == 0
    assert summary["overdue_milestones"] == 0
    assert isinstance(summary["days_to_close"], int)


def test_get_transaction_summary_not_found(db, svc):
    assert svc.get_transaction_summary(db, 99999) is None


# ── Update ──────────────────────────────────────────────────────


def test_update_milestone_status(db, svc, sample_property):
    txn = svc.create_transaction(db, property_id=sample_property.id)
    milestone = txn.milestones[0]

    updated = svc.update_milestone(db, milestone.id, status="completed", outcome_notes="All good")
    assert updated.status == MilestoneStatus.COMPLETED
    assert updated.outcome_notes == "All good"
    assert updated.completed_at is not None


def test_update_milestone_resets_reminder_sent(db, svc, sample_property):
    txn = svc.create_transaction(db, property_id=sample_property.id)
    milestone = txn.milestones[0]

    # Simulate reminder already sent
    milestone.reminder_sent = True
    db.commit()

    # Update status — should reset reminder_sent
    updated = svc.update_milestone(db, milestone.id, status="in_progress")
    assert updated.reminder_sent is False


def test_update_milestone_not_found(db, svc):
    assert svc.update_milestone(db, 99999, status="completed") is None


def test_advance_status_manual(db, svc, sample_property):
    txn = svc.create_transaction(db, property_id=sample_property.id)
    updated = svc.advance_status(db, txn.id, "inspections", notes="Moving to inspections")
    assert updated.status == TransactionStatus.INSPECTIONS
    assert "Moving to inspections" in updated.notes


def test_advance_status_to_closed_sets_closed_at(db, svc, sample_property):
    txn = svc.create_transaction(db, property_id=sample_property.id)
    updated = svc.advance_status(db, txn.id, "closed")
    assert updated.status == TransactionStatus.CLOSED
    assert updated.closed_at is not None


def test_advance_status_not_found(db, svc):
    assert svc.advance_status(db, 99999, "closed") is None


def test_auto_advance_on_milestone_completion(db, svc, sample_property):
    """When Attorney Review milestone is completed, status should auto-advance."""
    txn = svc.create_transaction(db, property_id=sample_property.id)

    # Find Attorney Review milestone
    atty = next(m for m in txn.milestones if m.name == "Attorney Review")
    svc.update_milestone(db, atty.id, status="completed")

    db.refresh(txn)
    assert txn.status == TransactionStatus.ATTORNEY_REVIEW


def test_auto_advance_multiple_milestones(db, svc, sample_property):
    """Completing multiple milestones should advance to the furthest matching status."""
    txn = svc.create_transaction(db, property_id=sample_property.id)

    milestone_map = {m.name: m for m in txn.milestones}

    # Complete Attorney Review + Home Inspection + Inspection Resolution
    svc.update_milestone(db, milestone_map["Attorney Review"].id, status="completed")
    svc.update_milestone(db, milestone_map["Home Inspection"].id, status="completed")
    svc.update_milestone(db, milestone_map["Inspection Resolution"].id, status="completed")

    db.refresh(txn)
    assert txn.status == TransactionStatus.INSPECTIONS


def test_add_party(db, svc, sample_property):
    txn = svc.create_transaction(db, property_id=sample_property.id)
    updated = svc.add_party(db, txn.id, "Bob Attorney", "attorney", "bob@law.com", "555-0001")
    assert len(updated.parties) == 1
    assert updated.parties[0]["name"] == "Bob Attorney"
    assert updated.parties[0]["role"] == "attorney"


def test_add_party_not_found(db, svc):
    assert svc.add_party(db, 99999, "Bob", "attorney") is None


def test_add_risk_flag(db, svc, sample_property):
    txn = svc.create_transaction(db, property_id=sample_property.id)
    updated = svc.add_risk_flag(db, txn.id, "appraisal_gap_risk")
    assert "appraisal_gap_risk" in updated.risk_flags


def test_add_risk_flag_no_duplicates(db, svc, sample_property):
    txn = svc.create_transaction(db, property_id=sample_property.id)
    svc.add_risk_flag(db, txn.id, "slow_lender")
    svc.add_risk_flag(db, txn.id, "slow_lender")
    db.refresh(txn)
    assert txn.risk_flags.count("slow_lender") == 1


def test_add_risk_flag_not_found(db, svc):
    assert svc.add_risk_flag(db, 99999, "test") is None


# ── Deadline Checker ────────────────────────────────────────────


def test_check_deadlines_no_active_transactions(db, svc):
    alerts = svc.check_deadlines(db)
    assert alerts == []


def test_check_deadlines_detects_overdue(db, svc, sample_property):
    """Milestones past due should be flagged as overdue."""
    past = datetime.now(timezone.utc) - timedelta(days=20)
    txn = svc.create_transaction(
        db,
        property_id=sample_property.id,
        accepted_date=past,
        closing_date=datetime.now(timezone.utc) + timedelta(days=30),
    )

    alerts = svc.check_deadlines(db)
    overdue = [a for a in alerts if a["type"] == "overdue"]
    assert len(overdue) > 0

    # The overdue milestones should have been marked
    for alert in overdue:
        milestone = db.query(TransactionMilestone).filter(
            TransactionMilestone.id == alert["milestone_id"]
        ).first()
        assert milestone.status == MilestoneStatus.OVERDUE
        assert milestone.reminder_sent is True


def test_check_deadlines_detects_upcoming(db, svc, sample_property):
    """Milestones due within 24 hours should be flagged as upcoming."""
    # Set accepted_date so Attorney Review (3 days) is due in ~12 hours
    accepted = datetime.now(timezone.utc) - timedelta(days=3) + timedelta(hours=12)
    txn = svc.create_transaction(
        db,
        property_id=sample_property.id,
        accepted_date=accepted,
        closing_date=datetime.now(timezone.utc) + timedelta(days=60),
    )

    alerts = svc.check_deadlines(db)
    upcoming = [a for a in alerts if a["type"] == "upcoming"]
    assert len(upcoming) > 0


def test_check_deadlines_dedup_no_double_alerts(db, svc, sample_property):
    """Once a milestone is marked overdue with reminder_sent=True, no second alert."""
    past = datetime.now(timezone.utc) - timedelta(days=20)
    txn = svc.create_transaction(
        db,
        property_id=sample_property.id,
        accepted_date=past,
        closing_date=datetime.now(timezone.utc) + timedelta(days=30),
    )

    # First run
    alerts1 = svc.check_deadlines(db)
    overdue_count_1 = len([a for a in alerts1 if a["type"] == "overdue"])

    # Second run — should not re-alert the same milestones
    alerts2 = svc.check_deadlines(db)
    overdue_count_2 = len([a for a in alerts2 if a["type"] == "overdue"])

    assert overdue_count_1 > 0
    assert overdue_count_2 == 0  # Already flagged, no new alerts


def test_check_deadlines_skips_completed_milestones(db, svc, sample_property):
    """Completed milestones should not generate alerts even if past due."""
    past = datetime.now(timezone.utc) - timedelta(days=20)
    txn = svc.create_transaction(
        db,
        property_id=sample_property.id,
        accepted_date=past,
        closing_date=datetime.now(timezone.utc) + timedelta(days=30),
    )

    # Complete all milestones
    for m in txn.milestones:
        m.status = MilestoneStatus.COMPLETED
        m.completed_at = datetime.now(timezone.utc)
    db.commit()

    alerts = svc.check_deadlines(db)
    assert alerts == []


def test_check_deadlines_skips_waived_milestones(db, svc, sample_property):
    past = datetime.now(timezone.utc) - timedelta(days=20)
    txn = svc.create_transaction(
        db,
        property_id=sample_property.id,
        accepted_date=past,
        closing_date=datetime.now(timezone.utc) + timedelta(days=30),
    )

    for m in txn.milestones:
        m.status = MilestoneStatus.WAIVED
    db.commit()

    alerts = svc.check_deadlines(db)
    assert alerts == []


def test_check_deadlines_ignores_terminal_transactions(db, svc, sample_property):
    """Closed/cancelled/fell-through transactions should be skipped."""
    past = datetime.now(timezone.utc) - timedelta(days=20)
    txn = svc.create_transaction(
        db,
        property_id=sample_property.id,
        accepted_date=past,
    )
    svc.advance_status(db, txn.id, "closed")

    alerts = svc.check_deadlines(db)
    assert alerts == []


# ── Pipeline Dashboard ──────────────────────────────────────────


def test_pipeline_empty(db, svc):
    pipeline = svc.get_pipeline(db)
    assert pipeline["active_count"] == 0
    assert pipeline["total_pipeline_value"] == 0.0
    assert pipeline["by_status"] == {}
    assert pipeline["upcoming_7_days"] == []


def test_pipeline_with_transactions(db, svc, sample_property, second_property):
    svc.create_transaction(db, property_id=sample_property.id, sale_price=300000)
    svc.create_transaction(db, property_id=second_property.id, sale_price=500000)

    pipeline = svc.get_pipeline(db)
    assert pipeline["active_count"] == 2
    assert pipeline["total_pipeline_value"] == 800000.0
    assert pipeline["by_status"]["initiated"] == 2


def test_pipeline_upcoming_milestones(db, svc, sample_property):
    """Milestones due within 7 days should appear in upcoming_7_days."""
    # Accepted 2 days ago — Attorney Review (3 days) is due tomorrow
    accepted = datetime.now(timezone.utc) - timedelta(days=2)
    svc.create_transaction(
        db,
        property_id=sample_property.id,
        accepted_date=accepted,
        closing_date=datetime.now(timezone.utc) + timedelta(days=60),
    )

    pipeline = svc.get_pipeline(db)
    assert len(pipeline["upcoming_7_days"]) > 0
