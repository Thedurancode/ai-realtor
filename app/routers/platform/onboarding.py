"""Onboarding questionnaire API router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.database import get_db
from app.services.onboarding_service import onboarding_service
from app.services.memory_graph import memory_graph_service


router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


# Pydantic models
class OnboardingQuestionResponse(BaseModel):
    question_id: str
    question: str
    type: str
    options: List[str] = []
    placeholder: Optional[str] = None
    required: bool
    category: str


class OnboardingAnswersSubmit(BaseModel):
    agent_id: int
    answers: Dict[str, Any]
    session_id: str


class OnboardingWelcomeRequest(BaseModel):
    agent_id: int
    session_id: str


@router.get("/questions", response_model=List[OnboardingQuestionResponse])
async def get_onboarding_questions(
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all onboarding questions, optionally filtered by category."""

    questions = onboarding_service.get_questions(category=category)
    return questions


@router.get("/categories")
async def get_onboarding_categories(db: Session = Depends(get_db)):
    """Get all onboarding question categories."""

    categories = onboarding_service.get_categories()
    return {
        "categories": categories,
        "total": len(categories)
    }


@router.post("/submit")
async def submit_onboarding_answers(
    submission: OnboardingAnswersSubmit,
    db: Session = Depends(get_db)
):
    """Submit agent's onboarding questionnaire answers."""

    result = await onboarding_service.save_onboarding_answers(
        db=db,
        agent_id=submission.agent_id,
        answers=submission.answers,
        session_id=submission.session_id
    )

    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))

    return result


@router.post("/welcome")
async def generate_welcome_message(
    request: OnboardingWelcomeRequest,
    db: Session = Depends(get_db)
):
    """Generate personalized welcome message based on onboarding answers."""

    result = await onboarding_service.generate_personalized_welcome(
        db=db,
        agent_id=request.agent_id,
        session_id=request.session_id
    )

    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))

    return result


@router.get("/status/{agent_id}")
async def get_onboarding_status(
    agent_id: int,
    session_id: str,
    db: Session = Depends(get_db)
):
    """Check if agent has completed onboarding."""

    # Get agent's memory summary
    summary = memory_graph_service.get_session_summary(db, session_id, max_nodes=1)

    # Check if identity exists (indicates onboarding started)
    identity_exists = any(
        node["node_type"] == "identity" and
        node["payload"].get("entity_type") == "agent"
        for node in summary.get("recent_nodes", [])
    )

    # Check for onboarding-specific memories
    onboarding_memories = [
        node for node in summary.get("recent_nodes", [])
        if node.get("payload", {}).get("kind") in ["fact", "preference", "goal"]
        and any(key in str(node.get("payload", {}))
               for key in ["brokerage", "experience", "primary_market", "monthly_goals"])
    ]

    return {
        "agent_id": agent_id,
        "onboarding_complete": len(onboarding_memories) >= 5,  # At least 5 onboarding answers
        "onboarding_progress": min(len(onboarding_memories) * 5, 100),  # Rough percentage
        "identity_exists": identity_exists,
        "total_memories": summary.get("node_count", 0)
    }


@router.get("/preview")
async def preview_onboarding_questions():
    """Preview all onboarding questions without authentication (for marketing page)."""

    questions = onboarding_service.get_questions()
    categories = onboarding_service.get_categories()

    # Group by category
    grouped = {}
    for q in questions:
        category = q["category"]
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(q)

    return {
        "total_questions": len(questions),
        "categories": categories,
        "questions_by_category": grouped
    }


class CompleteOnboardingRequest(BaseModel):
    """Complete onboarding request from landing page wizard."""
    first_name: str
    last_name: str
    age: Optional[int] = None
    city: str
    address: Optional[str] = None
    phone: str
    email: str
    schedule: Optional[Dict[str, Dict[str, str]]] = None
    weekend_schedule: Optional[Dict[str, Dict[str, str]]] = None
    business_name: str
    logo: Optional[str] = None
    colors: Optional[Dict[str, str]] = None
    contacts_file: Optional[str] = None
    social_media: Optional[Dict[str, str]] = None
    music_preferences: Optional[List[str]] = None
    contracts: Optional[List[str]] = None
    connect_calendar: Optional[bool] = False
    primary_market: str
    secondary_markets: Optional[str] = None
    service_radius: Optional[str] = None
    office_locations: Optional[str] = None
    assistant_name: str
    assistant_style: str
    personality: Optional[Dict[str, int]] = None


@router.post("/complete")
async def complete_onboarding(
    data: CompleteOnboardingRequest,
    db: Session = Depends(get_db)
):
    """Complete onboarding from landing page wizard and create agent account."""

    try:
        result = await onboarding_service.complete_onboarding_wizard(db=db, data=data)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
