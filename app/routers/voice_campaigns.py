"""Voice campaign management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.property import Property
from app.schemas.voice_campaign import (
    VoiceCampaignAnalyticsResponse,
    VoiceCampaignCreateRequest,
    VoiceCampaignEnrollResponse,
    VoiceCampaignProcessResponse,
    VoiceCampaignResponse,
    VoiceCampaignTargetFilterAddRequest,
    VoiceCampaignTargetManualAddRequest,
    VoiceCampaignTargetResponse,
    VoiceCampaignUpdateRequest,
)
from app.services.voice_campaign_service import voice_campaign_service


router = APIRouter(prefix="/voice-campaigns", tags=["voice-campaigns"])


def _require_campaign(db: Session, campaign_id: int):
    campaign = voice_campaign_service.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.post("/", response_model=VoiceCampaignResponse, status_code=201)
def create_campaign(request: VoiceCampaignCreateRequest, db: Session = Depends(get_db)):
    if request.property_id:
        prop = db.query(Property).filter(Property.id == request.property_id).first()
        if not prop:
            raise HTTPException(status_code=404, detail="Property not found")

    campaign = voice_campaign_service.create_campaign(
        db,
        name=request.name,
        description=request.description,
        call_purpose=request.call_purpose,
        property_id=request.property_id,
        contact_roles=request.contact_roles,
        max_attempts=request.max_attempts,
        retry_delay_minutes=request.retry_delay_minutes,
        rate_limit_per_minute=request.rate_limit_per_minute,
        assistant_overrides=request.assistant_overrides,
    )

    if request.auto_enroll_from_filters:
        voice_campaign_service.add_targets_from_filters(
            db,
            campaign=campaign,
            property_id=request.property_id,
            contact_roles=request.contact_roles,
            limit=500,
        )

    return campaign


@router.get("/", response_model=list[VoiceCampaignResponse])
def list_campaigns(status: str | None = None, limit: int = 100, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 1000))
    return voice_campaign_service.list_campaigns(db, status=status, limit=limit)


@router.get("/{campaign_id}", response_model=VoiceCampaignResponse)
def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    return _require_campaign(db, campaign_id)


@router.patch("/{campaign_id}", response_model=VoiceCampaignResponse)
def update_campaign(campaign_id: int, request: VoiceCampaignUpdateRequest, db: Session = Depends(get_db)):
    campaign = _require_campaign(db, campaign_id)

    updates = request.model_dump(exclude_unset=True)
    if "property_id" in updates and updates["property_id"]:
        prop = db.query(Property).filter(Property.id == updates["property_id"]).first()
        if not prop:
            raise HTTPException(status_code=404, detail="Property not found")

    return voice_campaign_service.update_campaign(db, campaign, updates)


@router.delete("/{campaign_id}", response_model=VoiceCampaignResponse)
def cancel_campaign(campaign_id: int, db: Session = Depends(get_db)):
    campaign = _require_campaign(db, campaign_id)
    return voice_campaign_service.cancel_campaign(db, campaign)


@router.post("/{campaign_id}/targets", response_model=VoiceCampaignEnrollResponse)
def add_targets_manual(
    campaign_id: int,
    request: VoiceCampaignTargetManualAddRequest,
    db: Session = Depends(get_db),
):
    campaign = _require_campaign(db, campaign_id)

    if not request.contact_ids and not request.phone_numbers:
        raise HTTPException(status_code=400, detail="Provide contact_ids or phone_numbers")

    summary = voice_campaign_service.add_targets_manual(
        db,
        campaign=campaign,
        contact_ids=request.contact_ids,
        phone_numbers=request.phone_numbers,
        property_id=request.property_id,
    )
    return VoiceCampaignEnrollResponse(**summary)


@router.post("/{campaign_id}/targets/from-filters", response_model=VoiceCampaignEnrollResponse)
def add_targets_from_filters(
    campaign_id: int,
    request: VoiceCampaignTargetFilterAddRequest,
    db: Session = Depends(get_db),
):
    campaign = _require_campaign(db, campaign_id)

    summary = voice_campaign_service.add_targets_from_filters(
        db,
        campaign=campaign,
        property_id=request.property_id,
        contact_roles=request.contact_roles,
        limit=request.limit,
    )
    return VoiceCampaignEnrollResponse(**summary)


@router.get("/{campaign_id}/targets", response_model=list[VoiceCampaignTargetResponse])
def list_targets(
    campaign_id: int,
    status: str | None = None,
    limit: int = 500,
    db: Session = Depends(get_db),
):
    _require_campaign(db, campaign_id)
    limit = max(1, min(limit, 5000))
    return voice_campaign_service.list_targets(db, campaign_id=campaign_id, status=status, limit=limit)


@router.post("/{campaign_id}/start", response_model=VoiceCampaignResponse)
def start_campaign(campaign_id: int, db: Session = Depends(get_db)):
    campaign = _require_campaign(db, campaign_id)
    try:
        return voice_campaign_service.start_campaign(db, campaign)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{campaign_id}/pause", response_model=VoiceCampaignResponse)
def pause_campaign(campaign_id: int, db: Session = Depends(get_db)):
    campaign = _require_campaign(db, campaign_id)
    return voice_campaign_service.pause_campaign(db, campaign)


@router.post("/{campaign_id}/resume", response_model=VoiceCampaignResponse)
def resume_campaign(campaign_id: int, db: Session = Depends(get_db)):
    campaign = _require_campaign(db, campaign_id)
    return voice_campaign_service.resume_campaign(db, campaign)


@router.post("/{campaign_id}/process", response_model=VoiceCampaignProcessResponse)
async def process_campaign(campaign_id: int, max_calls: int = 5, db: Session = Depends(get_db)):
    campaign = _require_campaign(db, campaign_id)
    max_calls = max(1, min(max_calls, 200))

    summary = await voice_campaign_service.process_campaign_once_locked(
        db,
        campaign=campaign,
        max_calls=max_calls,
    )

    return VoiceCampaignProcessResponse(
        campaigns_scanned=1,
        targets_processed=summary["targets_processed"],
        calls_started=summary["calls_started"],
        retries_scheduled=summary["retries_scheduled"],
        exhausted=summary["exhausted"],
    )


@router.post("/process", response_model=VoiceCampaignProcessResponse)
async def process_all_active_campaigns(max_calls_per_campaign: int = 5):
    max_calls_per_campaign = max(1, min(max_calls_per_campaign, 200))
    summary = await voice_campaign_service.process_active_campaigns_once(
        max_calls_per_campaign=max_calls_per_campaign,
    )
    return VoiceCampaignProcessResponse(**summary)


@router.get("/{campaign_id}/analytics", response_model=VoiceCampaignAnalyticsResponse)
def get_campaign_analytics(campaign_id: int, db: Session = Depends(get_db)):
    campaign = _require_campaign(db, campaign_id)
    stats = voice_campaign_service.get_campaign_analytics(db, campaign)
    return VoiceCampaignAnalyticsResponse(**stats)
