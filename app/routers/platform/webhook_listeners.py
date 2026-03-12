"""
Webhook Listener endpoints — receive, register, and test webhook events.

Provides instant event-driven processing instead of polling.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database import get_db
from app.models.webhook_registration import WebhookRegistration
from app.services.webhook_listener_service import (
    process_webhook,
    SUPPORTED_EVENT_TYPES,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/listeners", tags=["webhook-listeners"])


# ── Schemas ──────────────────────────────────────────────────────────────

class WebhookRegisterRequest(BaseModel):
    url: str
    event_type: str
    secret: Optional[str] = None


class WebhookRegisterResponse(BaseModel):
    id: int
    url: str
    event_type: str
    is_active: bool
    message: str


class WebhookTestRequest(BaseModel):
    payload: Optional[dict] = None


# ── Endpoints ────────────────────────────────────────────────────────────

@router.post("/incoming/{event_type}")
async def receive_webhook(
    event_type: str,
    request: Request,
    background_tasks: BackgroundTasks,
    x_webhook_secret: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Receive an incoming webhook event.

    Validates the optional X-Webhook-Secret header against registered webhooks,
    then queues processing in the background so the caller gets a fast 200.
    """
    if event_type not in SUPPORTED_EVENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported event type: {event_type}. Supported: {SUPPORTED_EVENT_TYPES}",
        )

    # Validate secret if any registrations for this event_type have one
    registrations = (
        db.query(WebhookRegistration)
        .filter(
            WebhookRegistration.event_type == event_type,
            WebhookRegistration.is_active == True,  # noqa: E712
            WebhookRegistration.secret.isnot(None),
        )
        .all()
    )

    if registrations:
        # At least one registration has a secret — require it
        secrets = {r.secret for r in registrations}
        if x_webhook_secret not in secrets:
            logger.warning(f"Invalid webhook secret for event_type={event_type}")
            raise HTTPException(status_code=401, detail="Invalid or missing X-Webhook-Secret")

    # Parse body
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Queue processing in the background
    background_tasks.add_task(process_webhook, event_type, payload)

    return {
        "status": "accepted",
        "event_type": event_type,
        "message": "Webhook event queued for processing",
    }


@router.post("/register", response_model=WebhookRegisterResponse)
async def register_webhook(
    body: WebhookRegisterRequest,
    db: Session = Depends(get_db),
):
    """Register a webhook URL to receive events of a given type."""
    if body.event_type not in SUPPORTED_EVENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported event type: {body.event_type}. Supported: {SUPPORTED_EVENT_TYPES}",
        )

    registration = WebhookRegistration(
        url=body.url,
        event_type=body.event_type,
        secret=body.secret,
        is_active=True,
    )
    db.add(registration)
    db.commit()
    db.refresh(registration)

    logger.info(f"Registered webhook #{registration.id}: {body.event_type} -> {body.url}")

    return WebhookRegisterResponse(
        id=registration.id,
        url=registration.url,
        event_type=registration.event_type,
        is_active=registration.is_active,
        message=f"Webhook registered for '{body.event_type}' events",
    )


@router.get("/registered")
async def list_registered_webhooks(
    event_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all registered webhooks, optionally filtered by event type."""
    query = db.query(WebhookRegistration)
    if event_type:
        query = query.filter(WebhookRegistration.event_type == event_type)
    registrations = query.order_by(WebhookRegistration.created_at.desc()).all()

    return [
        {
            "id": r.id,
            "url": r.url,
            "event_type": r.event_type,
            "is_active": r.is_active,
            "has_secret": r.secret is not None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in registrations
    ]


@router.post("/test/{event_type}")
async def test_webhook(
    event_type: str,
    body: Optional[WebhookTestRequest] = None,
    background_tasks: BackgroundTasks = None,
):
    """
    Send a test webhook event to exercise the processing pipeline.

    If no payload is provided, a sample payload is generated for the event type.
    """
    if event_type not in SUPPORTED_EVENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported event type: {event_type}. Supported: {SUPPORTED_EVENT_TYPES}",
        )

    sample_payloads = {
        "new_lead": {
            "address": "123 Test Street, Miami, FL 33101",
            "price": 450000,
            "source": "webhook_test",
            "contact_name": "Test Lead",
            "contact_phone": "555-0100",
        },
        "property_update": {
            "property_id": 1,
            "changes": {"price": 425000, "status": "under_contract"},
        },
        "offer_received": {
            "property_id": 1,
            "offer_price": 440000,
            "buyer_name": "Test Buyer",
            "financing_type": "conventional",
            "contingencies": ["inspection", "appraisal"],
            "closing_date": "2026-04-15",
        },
        "contract_signed": {
            "property_id": 1,
            "contract_name": "Purchase Agreement",
            "signer_name": "Test Signer",
            "signed_at": "2026-03-05T14:30:00Z",
        },
        "email_received": {
            "from_email": "test@example.com",
            "subject": "Interested in 123 Main St",
            "snippet": "Hi, I saw your listing and would like to schedule a showing...",
        },
        "mls_listing": {
            "address": "456 Sample Ave, Austin, TX 78701",
            "price": 375000,
            "bedrooms": 3,
            "bathrooms": 2,
            "sqft": 1800,
            "property_type": "single_family",
            "city": "Austin",
            "state": "TX",
            "mls_id": "MLS-TEST-001",
        },
    }

    payload = (body.payload if body and body.payload else None) or sample_payloads.get(event_type, {})

    # Process synchronously for test so caller sees results
    result = await process_webhook(event_type, payload)

    return {
        "status": "tested",
        "event_type": event_type,
        "payload_used": payload,
        "result": result,
    }
