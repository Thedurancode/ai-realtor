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

from app.database import get_db
from app.models import Contract, Property
from app.models.contract import ContractStatus
from app.services.property_recap_service import property_recap_service
from app.services.deal_type_service import get_deal_type_summary

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
