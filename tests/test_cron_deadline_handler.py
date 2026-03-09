"""Tests for transaction_deadline_handler cron task.

Covers:
- Handler creates notifications for overdue/upcoming milestones
- SMS is skipped when env vars are missing
- Email is skipped when RESEND_API_KEY is missing
- Handler returns correct counts
- Handler handles no-alert scenario
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, AsyncMock

from app.models.transaction import TransactionStatus, MilestoneStatus
from app.models.notification import Notification, NotificationType, NotificationPriority
from app.services.transaction_coordinator_service import TransactionCoordinatorService


@pytest.fixture()
def svc():
    return TransactionCoordinatorService()


@pytest.mark.asyncio
async def test_deadline_handler_no_alerts(db, svc, sample_property):
    """When no milestones are overdue/upcoming, handler returns zero counts."""
    from app.services.cron_tasks import transaction_deadline_handler

    # Create a transaction far in the future — nothing overdue
    future = datetime.now(timezone.utc) + timedelta(days=5)
    svc.create_transaction(
        db,
        property_id=sample_property.id,
        accepted_date=future,
        closing_date=future + timedelta(days=45),
    )

    result = await transaction_deadline_handler(db, {})
    assert result["alerts"] == 0
    assert result["overdue"] == 0
    assert result["upcoming"] == 0
    assert result["notifications_created"] == 0


@pytest.mark.asyncio
async def test_deadline_handler_creates_notifications(db, svc, sample_property):
    """Handler should create Notification records for each alert."""
    from app.services.cron_tasks import transaction_deadline_handler

    # Create overdue transaction
    past = datetime.now(timezone.utc) - timedelta(days=20)
    svc.create_transaction(
        db,
        property_id=sample_property.id,
        accepted_date=past,
        closing_date=datetime.now(timezone.utc) + timedelta(days=30),
    )

    # Patch SMS/email to avoid real API calls
    with patch("app.services.cron_tasks._send_deadline_sms", new_callable=AsyncMock, return_value=0), \
         patch("app.services.cron_tasks._send_deadline_email", new_callable=AsyncMock, return_value=False):
        result = await transaction_deadline_handler(db, {})

    assert result["alerts"] > 0
    assert result["notifications_created"] > 0
    assert result["overdue"] > 0

    # Verify notifications were persisted
    notifications = db.query(Notification).filter(
        Notification.type == NotificationType.TRANSACTION_DEADLINE
    ).all()
    assert len(notifications) == result["notifications_created"]

    # Overdue notifications should be URGENT priority
    overdue_notifs = [n for n in notifications if n.priority == NotificationPriority.URGENT]
    assert len(overdue_notifs) > 0


@pytest.mark.asyncio
async def test_deadline_handler_sms_skipped_no_env(db, svc, sample_property):
    """SMS should be skipped gracefully when TELNYX env vars are missing."""
    from app.services.cron_tasks import _send_deadline_sms

    alerts = [{"type": "overdue", "message": "Test overdue", "milestone": "Test"}]

    with patch.dict("os.environ", {"TELNYX_API_KEY": "", "OWNER_PHONE": "", "TELNYX_FROM_NUMBER": ""}, clear=False):
        result = await _send_deadline_sms(alerts)
    assert result == 0


@pytest.mark.asyncio
async def test_deadline_handler_email_skipped_no_env(db, svc):
    """Email should be skipped gracefully when RESEND_API_KEY is missing."""
    from app.services.cron_tasks import _send_deadline_email

    alerts = [{"type": "overdue", "message": "Test", "milestone": "Test"}]

    with patch.dict("os.environ", {"RESEND_API_KEY": ""}, clear=False):
        result = await _send_deadline_email(alerts)
    assert result is False


@pytest.mark.asyncio
async def test_deadline_handler_returns_details(db, svc, sample_property):
    """Result should include details of top alerts."""
    from app.services.cron_tasks import transaction_deadline_handler

    past = datetime.now(timezone.utc) - timedelta(days=20)
    svc.create_transaction(
        db,
        property_id=sample_property.id,
        accepted_date=past,
        closing_date=datetime.now(timezone.utc) + timedelta(days=30),
    )

    with patch("app.services.cron_tasks._send_deadline_sms", new_callable=AsyncMock, return_value=0), \
         patch("app.services.cron_tasks._send_deadline_email", new_callable=AsyncMock, return_value=False):
        result = await transaction_deadline_handler(db, {})

    assert "details" in result
    assert len(result["details"]) > 0
    assert "milestone" in result["details"][0]
    assert "type" in result["details"][0]


@pytest.mark.asyncio
async def test_deadline_handler_dedup_across_runs(db, svc, sample_property):
    """Running the handler twice should not create duplicate notifications."""
    from app.services.cron_tasks import transaction_deadline_handler

    past = datetime.now(timezone.utc) - timedelta(days=20)
    svc.create_transaction(
        db,
        property_id=sample_property.id,
        accepted_date=past,
        closing_date=datetime.now(timezone.utc) + timedelta(days=30),
    )

    with patch("app.services.cron_tasks._send_deadline_sms", new_callable=AsyncMock, return_value=0), \
         patch("app.services.cron_tasks._send_deadline_email", new_callable=AsyncMock, return_value=False):
        result1 = await transaction_deadline_handler(db, {})
        result2 = await transaction_deadline_handler(db, {})

    # First run creates notifications, second run should find none
    assert result1["notifications_created"] > 0
    assert result2["alerts"] == 0
    assert result2["notifications_created"] == 0
