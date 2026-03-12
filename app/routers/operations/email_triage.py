"""
Email Triage Router

Endpoints for email auto-triage: check inbox, classify, draft replies, view digest.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.email_triage import TriagedEmail
from app.services.email_triage_service import email_triage_service

router = APIRouter(
    prefix="/email/triage",
    tags=["Email Triage"],
)


# ---------- Schemas ----------

class EmailCheckRequest(BaseModel):
    since_minutes: int = Field(default=30, ge=1, le=1440, description="How far back to check (minutes)")


class EmailClassifyRequest(BaseModel):
    subject: str
    body: str
    from_address: str = ""
    from_name: str = ""


class EmailDraftRequest(BaseModel):
    subject: str
    body: str
    from_address: str = ""
    from_name: str = ""
    classification: str = "warm_lead"


class ClassificationResponse(BaseModel):
    classification: str
    priority: int
    reasoning: str
    key_details: str


class DraftResponse(BaseModel):
    drafted_response: str
    classification: str


class DigestResponse(BaseModel):
    digest: str
    total_processed: int


class StatsResponse(BaseModel):
    total_processed: int
    by_category: dict
    emails: list


# ---------- Endpoints ----------

@router.post("/check")
async def check_emails(
    request: EmailCheckRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Manually trigger an email check and triage.

    Fetches unread emails from the last `since_minutes` minutes,
    classifies each one, auto-drafts replies for leads, and sends
    Telegram alerts for high-priority items.
    """
    results = await email_triage_service.check_new_emails(since_minutes=request.since_minutes)

    # Persist triaged emails to DB in the background
    def _persist():
        for email_data in results:
            existing = db.query(TriagedEmail).filter(
                TriagedEmail.gmail_id == email_data.get("gmail_id")
            ).first()
            if existing:
                continue
            record = TriagedEmail(
                gmail_id=email_data.get("gmail_id"),
                from_address=email_data.get("from_address", ""),
                from_name=email_data.get("from_name"),
                subject=email_data.get("subject", ""),
                body_preview=email_data.get("body_preview", "")[:500],
                classification=email_data.get("classification", "general"),
                priority=email_data.get("priority", 4),
                drafted_response=email_data.get("drafted_response"),
                response_sent=False,
                processed_at=datetime.utcnow(),
            )
            db.add(record)
        db.commit()

    if results:
        background_tasks.add_task(_persist)

    return {
        "status": "ok",
        "emails_processed": len(results),
        "summary": {
            cat: len([e for e in results if e.get("classification") == cat])
            for cat in ["hot_lead", "warm_lead", "contract_update", "showing_request", "spam", "general"]
            if any(e.get("classification") == cat for e in results)
        },
    }


@router.get("/digest", response_model=DigestResponse)
async def get_digest():
    """Get current email digest / summary."""
    digest = email_triage_service.get_email_digest()
    stats = email_triage_service.get_stats()
    return DigestResponse(
        digest=digest,
        total_processed=stats["total_processed"],
    )


@router.post("/classify", response_model=ClassificationResponse)
async def classify_email(request: EmailClassifyRequest):
    """Classify a single email by subject + body."""
    email_data = {
        "subject": request.subject,
        "body": request.body,
        "from_address": request.from_address,
        "from_name": request.from_name,
    }
    result = await email_triage_service.classify_email(email_data)
    return ClassificationResponse(
        classification=result.get("classification", "general"),
        priority=result.get("priority", 4),
        reasoning=result.get("reasoning", ""),
        key_details=result.get("key_details", ""),
    )


@router.post("/draft-reply", response_model=DraftResponse)
async def draft_reply(request: EmailDraftRequest):
    """Draft a reply for an email."""
    email_data = {
        "subject": request.subject,
        "body": request.body,
        "from_address": request.from_address,
        "from_name": request.from_name,
    }
    draft = await email_triage_service.draft_response(email_data, request.classification)
    if not draft:
        raise HTTPException(status_code=500, detail="Failed to generate draft response")
    return DraftResponse(
        drafted_response=draft,
        classification=request.classification,
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    """Email stats: counts by category, recent emails."""
    # Combine in-memory stats with DB records
    in_memory = email_triage_service.get_stats()

    # Also pull DB counts
    db_counts = {}
    for row in db.query(
        TriagedEmail.classification,
    ).all():
        cat = row[0]
        db_counts[cat] = db_counts.get(cat, 0) + 1

    # Merge — in-memory takes precedence for session, DB adds historical
    merged_cats = dict(in_memory["by_category"])
    for cat, count in db_counts.items():
        if cat not in merged_cats or merged_cats[cat] == 0:
            merged_cats[cat] = count

    total_db = db.query(TriagedEmail).count()

    return StatsResponse(
        total_processed=max(in_memory["total_processed"], total_db),
        by_category=merged_cats,
        emails=in_memory["emails"],
    )
