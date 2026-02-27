"""
Webhook endpoints for external integrations.
Handles webhooks from DocuSeal and other services.
"""

from fastapi import APIRouter, Request, HTTPException, Depends, Header, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
import hmac
import hashlib
import logging
import os

from app.config import settings
from app.database import get_db
from app.models import Contract, Property
from app.models.contract import ContractStatus
from app.services.property_recap_service import property_recap_service
from app.services.deal_type_service import get_deal_type_summary
from app.services.voice_campaign_service import voice_campaign_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def verify_docuseal_signature(payload: bytes, signature: Optional[str], secret: str) -> bool:
    """
    Verify DocuSeal webhook signature using HMAC-SHA256.

    DocuSeal sends signature in X-DocuSeal-Signature header.
    Format: sha256=<hex_digest>
    """
    if not signature:
        logger.warning("No signature provided in webhook request")
        return False

    if not secret:
        logger.error("DOCUSEAL_WEBHOOK_SECRET not configured")
        return False

    # Remove 'sha256=' prefix if present
    if signature.startswith('sha256='):
        signature = signature[7:]

    # Calculate expected signature
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()

    # Compare signatures using constant-time comparison
    return hmac.compare_digest(expected_signature, signature)


def verify_vapi_signature(payload: bytes, signature: Optional[str], secret: str) -> bool:
    """
    Verify Vapi webhook signature using HMAC-SHA256.

    Supports either raw hex digest or `sha256=<hex_digest>` format.
    """
    if not signature or not secret:
        return False

    normalized = signature[7:] if signature.startswith("sha256=") else signature
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected_signature, normalized)


async def process_contract_signed(db: Session, event_data: dict):
    """
    Process contract signed event.
    Updates contract status and regenerates property recap.
    """
    submission_id = event_data.get('data', {}).get('id')
    template_id = event_data.get('data', {}).get('template', {}).get('id')
    status = event_data.get('data', {}).get('status')

    logger.info(f"Processing DocuSeal webhook: submission_id={submission_id}, template_id={template_id}, status={status}")

    # Find contract by docuseal_submission_id
    contract = db.query(Contract).filter(Contract.docuseal_submission_id == str(submission_id)).first()

    if not contract:
        logger.warning(f"No contract found with docuseal_submission_id={submission_id}")
        # Try to find by template_id if submission not found
        contract = db.query(Contract).filter(Contract.docuseal_template_id == str(template_id)).first()

        if contract:
            # Update with submission ID
            contract.docuseal_submission_id = str(submission_id)
            logger.info(f"Updated contract {contract.id} with docuseal_submission_id={submission_id}")

    if not contract:
        logger.error(f"Contract not found for submission {submission_id} or template {template_id}")
        return

    # Update contract status based on DocuSeal status
    old_status = contract.status

    if status == 'completed':
        contract.status = ContractStatus.COMPLETED
    elif status == 'pending':
        contract.status = ContractStatus.PENDING_SIGNATURE
    elif status == 'archived':
        contract.status = ContractStatus.ARCHIVED

    db.commit()

    logger.info(f"Updated contract {contract.id} status from {old_status} to {contract.status}")

    # Regenerate property recap with new contract status
    if contract.property_id:
        property = db.query(Property).filter(Property.id == contract.property_id).first()
        if property:
            logger.info(f"Regenerating recap for property {property.id} after contract update")
            await property_recap_service.generate_recap(
                db=db,
                property=property,
                trigger=f"contract_signed:{contract.name}"
            )
            logger.info(f"Property recap regenerated successfully")

            # Check deal type progress after contract update
            if property.deal_type:
                deal_summary = get_deal_type_summary(db, property)
                contracts_info = deal_summary.get("contracts", {})
                completed = contracts_info.get("completed", 0)
                total = contracts_info.get("total", 0)
                ready = deal_summary.get("ready_to_close", False)

                logger.info(
                    f"Deal status ({deal_summary.get('deal_type')}): "
                    f"{completed}/{total} contracts complete, "
                    f"ready_to_close={ready}"
                )

                # Log activity event for deal progress
                try:
                    from app.models.activity_event import ActivityEvent
                    event_description = (
                        f"{deal_summary.get('deal_type')}: {contract.name} signed "
                        f"({completed}/{total} contracts complete)"
                    )
                    if ready:
                        event_description += " - READY TO CLOSE!"

                    activity = ActivityEvent(
                        event_type="deal_progress",
                        tool_name="docuseal_webhook",
                        user_source="DocuSeal Webhook",
                        description=event_description,
                        status="success",
                        metadata={
                            "property_id": property.id,
                            "property_address": property.address,
                            "deal_type": deal_summary.get("deal_type_name"),
                            "contract_name": contract.name,
                            "contracts_completed": completed,
                            "contracts_total": total,
                            "ready_to_close": ready,
                            "missing_contacts": deal_summary.get("contacts", {}).get("missing_roles", []),
                        },
                    )
                    db.add(activity)
                    db.commit()
                except Exception as e:
                    logger.warning(f"Failed to log deal progress activity: {e}")


@router.post("/docuseal")
async def docuseal_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    x_docuseal_signature: Optional[str] = Header(None)
):
    """
    Receive DocuSeal webhook events.

    Events:
    - submission.created: New submission created
    - submission.completed: All signers completed
    - submission.archived: Submission archived
    - submission.viewed: Submission viewed by signer
    - submission.signed: Individual signer completed

    Returns:
        dict: Status message
    """
    # Get raw body for signature verification
    body = await request.body()

    # Verify webhook signature (optional for self-hosted DocuSeal)
    webhook_secret = os.getenv('DOCUSEAL_WEBHOOK_SECRET', '')

    if webhook_secret and x_docuseal_signature:
        # Only verify if both secret and signature are present
        is_valid = verify_docuseal_signature(body, x_docuseal_signature, webhook_secret)
        if not is_valid:
            logger.error("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")
        logger.info("Webhook signature verified successfully")
    elif webhook_secret and not x_docuseal_signature:
        # Self-hosted DocuSeal might not send signatures
        logger.warning("Webhook secret configured but no signature provided - allowing (self-hosted mode)")
    else:
        logger.warning("DOCUSEAL_WEBHOOK_SECRET not set - skipping signature verification")

    # Parse webhook payload
    try:
        event_data = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = event_data.get('event_type')

    logger.info(f"Received DocuSeal webhook: event_type={event_type}")

    # Process based on event type
    if event_type in ['submission.completed', 'submission.signed']:
        # Process in background to return 200 quickly
        background_tasks.add_task(process_contract_signed, db, event_data)
    elif event_type == 'submission.created':
        logger.info(f"Contract submission created: {event_data.get('data', {}).get('id')}")
    elif event_type == 'submission.archived':
        background_tasks.add_task(process_contract_signed, db, event_data)
    else:
        logger.warning(f"Unhandled event type: {event_type}")

    return {
        "status": "received",
        "event_type": event_type,
        "message": "Webhook processed successfully"
    }


@router.post("/vapi")
async def vapi_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_vapi_signature: Optional[str] = Header(None),
):
    """
    Receive Vapi webhook events and map outcomes to campaign targets.
    """
    body = await request.body()

    if settings.vapi_webhook_secret:
        is_valid = verify_vapi_signature(
            payload=body,
            signature=x_vapi_signature,
            secret=settings.vapi_webhook_secret,
        )
        if not is_valid:
            raise HTTPException(status_code=401, detail="Invalid Vapi webhook signature")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    result = voice_campaign_service.handle_vapi_webhook(db, payload)
    return {
        "status": "received",
        "result": result,
    }


@router.get("/docuseal/test")
def test_docuseal_webhook():
    """
    Test endpoint to verify webhook configuration.
    Returns webhook URL and configuration status.
    """
    webhook_secret_set = bool(os.getenv('DOCUSEAL_WEBHOOK_SECRET'))

    return {
        "webhook_url": "/webhooks/docuseal",
        "webhook_secret_configured": webhook_secret_set,
        "supported_events": [
            "submission.created",
            "submission.completed",
            "submission.signed",
            "submission.archived",
            "submission.viewed"
        ],
        "instructions": {
            "1": "Set DOCUSEAL_WEBHOOK_SECRET environment variable",
            "2": "Configure webhook URL in DocuSeal: https://your-domain.com/webhooks/docuseal",
            "3": "Select events to subscribe to in DocuSeal settings",
            "4": "DocuSeal will send X-DocuSeal-Signature header for verification"
        }
    }


# =========================================================================
# LOB WEBHOOKS
# =========================================================================

@router.post("/lob")
async def lob_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_lob_signature: Optional[str] = Header(None, alias="x-lob-signature"),
    db: Session = Depends(get_db)
):
    """
    Receive Lob.com webhook events for mailpiece tracking.

    Lob Event Types:
    - postcard.processed: Postcard has been processed
    - postcard.mailed: Postcard has been mailed
    - postcard.in_transit: Postcard is in transit
    - postcard.delivered: Postcard has been delivered
    - letter.processed: Letter has been processed
    - letter.mailed: Letter has been mailed
    - letter.in_transit: Letter is in transit
    - letter.delivered: Letter has been delivered
    - check.*: Check events

    Webhook Configuration in Lob Dashboard:
    1. Go to lob.com/dashboard -> Webhooks
    2. Add webhook URL: https://your-domain.com/webhooks/lob
    3. Select events to subscribe to
    4. Copy the webhook secret and set LOB_WEBHOOK_SECRET env variable
    5. Lob sends events as JSON POST requests with HMAC signature

    Security:
    - Verifies HMAC-SHA256 signature if LOB_WEBHOOK_SECRET is set
    - Signature format: sha256=<hmac_hash>
    - Prevents webhook spoofing

    Returns:
        dict: Status message
    """
    # Get raw body for signature verification
    body = await request.body()

    # Verify webhook signature if secret is configured
    if settings.lob_webhook_secret:
        if not x_lob_signature:
            logger.warning("Lob webhook received without signature")
            raise HTTPException(status_code=401, detail="Missing signature header")

        # Verify HMAC-SHA256 signature
        # Lob sends signature as: sha256=<hash>
        if not x_lob_signature.startswith("sha256="):
            raise HTTPException(status_code=401, detail="Invalid signature format")

        received_hash = x_lob_signature.split("=", 1)[1]

        # Calculate expected HMAC
        expected_hmac = hmac.new(
            settings.lob_webhook_secret.encode(),
            body,
            hashlib.sha256
        )
        expected_hash = expected_hmac.hexdigest()

        # Constant-time comparison to prevent timing attacks
        if not hmac.compare_digest(expected_hash, received_hash):
            logger.warning(f"Invalid Lob webhook signature: expected={expected_hash}, received={received_hash}")
            raise HTTPException(status_code=401, detail="Invalid signature")

        logger.debug("Lob webhook signature verified successfully")

    # Parse JSON payload
    try:
        event_data = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse Lob webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = event_data.get('event_type')
    event_id = event_data.get('id')
    resource_type = event_data.get('resource', {}).get('type')
    resource_data = event_data.get('data', {})

    logger.info(f"Received Lob webhook: event_type={event_type}, resource_type={resource_type}, id={event_id}")

    # Extract mailpiece ID
    mailpiece_id = resource_data.get('id')
    lob_object_id = event_id

    if not mailpiece_id:
        logger.warning(f"No mailpiece ID in webhook event {event_id}")
        return {"status": "received", "message": "No mailpiece ID found"}

    # Find our direct mail record
    from app.models.direct_mail import DirectMail, MailType, MailStatus

    # Try to find by lob_mailpiece_id or lob_object_id
    mailpiece = db.query(DirectMail).filter(
        DirectMail.lob_mailpiece_id == mailpiece_id
    ).first()

    if not mailpiece:
        # Try to find by lob_object_id
        mailpiece = db.query(DirectMail).filter(
            DirectMail.lob_object_id == lob_object_id
        ).first()

    if not mailpiece:
        logger.warning(f"No direct mail record found for Lob mailpiece {mailpiece_id}")
        return {"status": "received", "message": "Mailpiece not found in database"}

    # Process event
    try:
        if event_type == 'postcard.delivered' or event_type == 'letter.delivered':
            mailpiece.mail_status = MailStatus.DELIVERED
            mailpiece.delivered_at = None  # Will be set from event data if available

            # Extract tracking events
            tracking_events = resource_data.get('tracking_events', [])
            if tracking_events:
                mailpiece.tracking_events = tracking_events

            # Get tracking URL
            mailpiece.tracking_url = resource_data.get('tracking_url')

            logger.info(f"Mailpiece {mailpiece.id} marked as delivered")

            # Create notification
            try:
                from app.models.notification import Notification
                from app.models.activity_event import ActivityEvent

                notification = Notification(
                    agent_id=mailpiece.agent_id,
                    title=f"Direct Mail Delivered",
                    message=f"Your {mailpiece.mail_type.value} to {mailpiece.to_address.get('name', 'Recipient')} has been delivered.",
                    notification_type="direct_mail_delivered",
                    priority="low",
                    metadata={
                        "mailpiece_id": mailpiece.id,
                        "mail_type": mailpiece.mail_type.value,
                        "property_id": mailpiece.property_id,
                        "contact_id": mailpiece.contact_id
                    }
                )
                db.add(notification)

                # Log activity
                activity = ActivityEvent(
                    event_type="direct_mail_delivered",
                    tool_name="lob_webhook",
                    user_source="Lob Webhook",
                    description=f"{mailpiece.mail_type.value} delivered via Lob (Mailpiece ID: {mailpiece.id})",
                    status="success",
                    metadata={
                        "mailpiece_id": mailpiece.id,
                        "property_id": mailpiece.property_id,
                        "contact_id": mailpiece.contact_id
                    }
                )
                db.add(activity)

            except Exception as e:
                logger.warning(f"Failed to create notification/activity: {e}")

        elif event_type == 'postcard.in_transit' or event_type == 'letter.in_transit':
            mailpiece.mail_status = MailStatus.IN_TRANSIT

            # Update tracking events
            tracking_events = resource_data.get('tracking_events', [])
            if tracking_events:
                mailpiece.tracking_events = tracking_events

            logger.info(f"Mailpiece {mailpiece.id} marked as in transit")

        elif event_type == 'postcard.mailed' or event_type == 'letter.mailed':
            mailpiece.mail_status = MailStatus.MAILED

            # Update expected delivery if available
            expected_delivery = resource_data.get('expected_delivery_date')
            if expected_delivery:
                from datetime import datetime
                try:
                    mailpiece.expected_delivery_date = datetime.fromisoformat(expected_delivery)
                except:
                    pass

            logger.info(f"Mailpiece {mailpiece.id} marked as mailed")

        elif event_type == 'postcard.processed' or event_type == 'letter.processed':
            mailpiece.mail_status = MailStatus.PROCESSING
            logger.info(f"Mailpiece {mailpiece.id} marked as processed")

        elif event_type == 'postcard.cancelled' or event_type == 'letter.cancelled':
            mailpiece.mail_status = MailStatus.CANCELLED
            logger.info(f"Mailpiece {mailpiece.id} marked as cancelled")

        elif event_type == 'postcard.production_failed' or event_type == 'letter.production_failed':
            mailpiece.mail_status = MailStatus.FAILED
            logger.error(f"Mailpiece {mailpiece.id} production failed")

        db.commit()

    except Exception as e:
        logger.error(f"Failed to process Lob webhook event: {e}")
        db.rollback()

    return {
        "status": "received",
        "event_type": event_type,
        "message": "Webhook processed successfully"
    }


@router.get("/lob/test")
def test_lob_webhook():
    """
    Test endpoint to verify Lob webhook configuration.
    Returns webhook URL and configuration instructions.
    """
    return {
        "webhook_url": "/webhooks/lob",
        "signature_verification": "enabled" if settings.lob_webhook_secret else "disabled",
        "supported_events": [
            "postcard.processed",
            "postcard.mailed",
            "postcard.in_transit",
            "postcard.delivered",
            "postcard.cancelled",
            "postcard.production_failed",
            "letter.processed",
            "letter.mailed",
            "letter.in_transit",
            "letter.delivered",
            "letter.cancelled",
            "letter.production_failed",
            "check.*"
        ],
        "configuration_steps": [
            "Go to lob.com/dashboard -> Webhooks",
            "Add webhook URL: https://your-domain.com/webhooks/lob",
            "Select events to subscribe to",
            "Copy the webhook signing key",
            "Set LOB_WEBHOOK_SECRET environment variable to the signing key",
            "Webhook signatures will be automatically verified"
        ],
        "signature_format": "x-lob-signature: sha256=<hmac_hash>",
        "signature_algorithm": "HMAC-SHA256",
        "example_events": {
            "postcard_delivered": {
                "id": "evt_abc123",
                "event_type": "postcard.delivered",
                "resource": {"type": "postcard"},
                "data": {
                    "id": "lob_abc123",
                    "expected_delivery_date": "2026-02-28",
                    "tracking_events": [
                        {"event": "processed", "time": "2026-02-26T10:00:00Z"},
                        {"event": "in_transit", "time": "2026-02-27T08:00:00Z"},
                        {"event": "delivered", "time": "2026-02-28T14:30:00Z"}
                    ],
                    "tracking_url": "https://lob.com/tracking/lob_abc123"
                }
            },
            "letter_mailed": {
                "id": "evt_def456",
                "event_type": "letter.mailed",
                "resource": {"type": "letter"},
                "data": {
                    "id": "lob_def456",
                    "expected_delivery_date": "2026-03-01",
                    "tracking_url": "https://lob.com/tracking/lob_def456"
                }
            }
        }
    }
