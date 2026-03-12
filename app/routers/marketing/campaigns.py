"""Campaign router - automated email/text drip campaigns."""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.campaign_service import campaign_service

router = APIRouter(prefix="/campaigns", tags=["campaigns"])
logger = logging.getLogger(__name__)


# ── Schemas ──────────────────────────────────────────────────────────

class CampaignCreate(BaseModel):
    agent_id: int
    name: str
    campaign_type: str = Field(..., description="lead_nurture, contract_reminder, open_house, market_report")
    target_contacts: List[int] = Field(..., description="List of contact IDs")
    target_properties: Optional[List[int]] = None
    custom_message: Optional[str] = None
    channels: Optional[List[str]] = None  # ["email", "sms"]


class CampaignSend(BaseModel):
    campaign_id: str
    touch_index: int = 0


class ContractReminderSchedule(BaseModel):
    agent_id: int
    contract_id: int
    deadline: str  # ISO format datetime
    contact_id: int


class MarketReportSend(BaseModel):
    agent_id: int
    contacts: List[int]
    market_data: dict


class CampaignCostEstimate(BaseModel):
    contacts_count: int
    touches_count: int
    channels: List[str]


# ── Endpoints ────────────────────────────────────────────────────────

@router.post("/")
def create_campaign(body: CampaignCreate, db: Session = Depends(get_db)):
    """Create a new automated campaign."""
    try:
        campaign = campaign_service.create_campaign(
            db=db,
            agent_id=body.agent_id,
            name=body.name,
            campaign_type=body.campaign_type,
            target_contacts=body.target_contacts,
            target_properties=body.target_properties,
            custom_message=body.custom_message,
            channels=body.channels
        )
        return campaign
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/send")
def send_campaign_touch(body: CampaignSend, db: Session = Depends(get_db)):
    """Send a specific touch from a campaign."""
    # For now, return success (would fetch from db in production)
    return {
        "message": "Campaign touch sent",
        "campaign_id": body.campaign_id,
        "touch_index": body.touch_index
    }


@router.post("/schedule-contract-reminders")
def schedule_contract_reminders(body: ContractReminderSchedule, db: Session = Depends(get_db)):
    """Schedule automatic contract deadline reminders."""
    from datetime import datetime

    deadline = datetime.fromisoformat(body.deadline)

    reminders = campaign_service.schedule_contract_reminders(
        db=db,
        agent_id=body.agent_id,
        contract_id=body.contract_id,
        deadline=deadline,
        contact_id=body.contact_id
    )

    return {
        "message": f"Scheduled {len(reminders)} reminders",
        "reminders": reminders
    }


@router.post("/send-market-report")
def send_market_report(body: MarketReportSend, db: Session = Depends(get_db)):
    """Send monthly market report to contacts."""
    result = campaign_service.send_market_report(
        db=db,
        agent_id=body.agent_id,
        contacts=body.contacts,
        market_data=body.market_data
    )
    return result


@router.post("/estimate-cost")
def estimate_campaign_cost(body: CampaignCostEstimate, db: Session = Depends(get_db)):
    """Estimate the cost of a campaign."""
    cost = campaign_service.estimate_campaign_cost(
        db=db,
        contacts_count=body.contacts_count,
        touches_count=body.touches_count,
        channels=body.channels
    )
    return cost


@router.get("/templates")
def get_campaign_templates():
    """Get all available campaign templates."""
    templates = campaign_service.get_campaign_templates()
    return templates


@router.get("/types")
def list_campaign_types():
    """List all available campaign types with descriptions."""
    types = {
        "lead_nurture": {
            "name": "Lead Nurture",
            "description": "7 touches over 30 days to nurture leads",
            "touches": 7,
            "duration_days": 30,
            "channels": ["email", "sms"]
        },
        "contract_reminder": {
            "name": "Contract Reminder",
            "description": "3 reminders leading up to contract deadline",
            "touches": 3,
            "duration_days": 3,
            "channels": ["sms"]
        },
        "open_house": {
            "name": "Open House Reminder",
            "description": "3 reminders before open house event",
            "touches": 3,
            "duration_days": 7,
            "channels": ["email", "sms"]
        },
        "market_report": {
            "name": "Monthly Market Report",
            "description": "Send monthly market statistics to contacts",
            "touches": 1,
            "duration_days": 30,
            "channels": ["email"]
        }
    }
    return types
