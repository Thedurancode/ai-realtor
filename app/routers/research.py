"""
Research Router

Endpoints for triggering comprehensive research across multiple services.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app.models.property import Property
from app.models.research import Research, ResearchStatus, ResearchType
from app.services.research_service import research_service
from app.schemas.research import ResearchCreateRequest, ResearchResponse, AIResearchRequest, APIEndpointConfig, APIResearchRequest


router = APIRouter(prefix="/research", tags=["research"])


# ========== Endpoints ==========

@router.post("/", response_model=ResearchResponse, status_code=201)
async def create_research(
    request: ResearchCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create and start a research job.

    The research will run in the background and you can poll the status.

    Research Types:
    - property_analysis: Complete property deep dive (Zillow, compliance, contracts, AI)
    - market_analysis: Market trends and comparable properties
    - compliance_check: Comprehensive compliance validation
    - contract_analysis: Contract requirements and gaps
    - owner_research: Skip trace and owner information
    - neighborhood_analysis: Area research and demographics
    - custom: Custom research with specified endpoints

    Example:
    {
        "research_type": "property_analysis",
        "property_id": 1
    }
    """
    # Validate property exists if provided
    if request.property_id:
        property = db.query(Property).filter(Property.id == request.property_id).first()
        if not property:
            raise HTTPException(status_code=404, detail="Property not found")

    # Create research job
    research = Research(
        research_type=request.research_type,
        property_id=request.property_id,
        agent_id=request.agent_id,
        parameters=request.parameters,
        endpoints_to_call=request.endpoints_to_call,
        status=ResearchStatus.PENDING
    )
    db.add(research)
    db.commit()
    db.refresh(research)

    # Start research in background
    background_tasks.add_task(research_service.perform_research, db, research)

    return research


@router.get("/{research_id}", response_model=ResearchResponse)
def get_research(research_id: int, db: Session = Depends(get_db)):
    """
    Get research job status and results.

    Poll this endpoint to check progress:
    - status: pending, in_progress, completed, failed
    - progress: 0-100 percentage
    - current_step: What's currently being processed
    - results: Full results when completed
    """
    research = db.query(Research).filter(Research.id == research_id).first()
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")

    return research


@router.get("/", response_model=List[ResearchResponse])
def list_research(
    property_id: Optional[int] = None,
    agent_id: Optional[int] = None,
    status: Optional[ResearchStatus] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    List research jobs with optional filters.

    Query params:
    - property_id: Filter by property
    - agent_id: Filter by agent
    - status: Filter by status (pending, in_progress, completed, failed)
    - limit: Max results (default 20)
    """
    query = db.query(Research)

    if property_id:
        query = query.filter(Research.property_id == property_id)
    if agent_id:
        query = query.filter(Research.agent_id == agent_id)
    if status:
        query = query.filter(Research.status == status)

    return query.order_by(Research.created_at.desc()).limit(limit).all()


@router.delete("/{research_id}", status_code=204)
def delete_research(research_id: int, db: Session = Depends(get_db)):
    """Delete a research job"""
    research = db.query(Research).filter(Research.id == research_id).first()
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")

    db.delete(research)
    db.commit()


# ========== Convenience Endpoints ==========

@router.post("/property/{property_id}/deep-dive", response_model=ResearchResponse)
async def property_deep_dive(
    property_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Quick endpoint to run complete property analysis.

    This is a convenience wrapper for:
    POST /research/ with research_type=property_analysis

    Performs:
    1. Zillow enrichment
    2. Skip trace
    3. Compliance check
    4. Contract analysis
    5. AI recommendations

    Results available at: GET /research/{id}
    """
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    research = Research(
        research_type=ResearchType.PROPERTY_ANALYSIS,
        property_id=property_id,
        status=ResearchStatus.PENDING
    )
    db.add(research)
    db.commit()
    db.refresh(research)

    background_tasks.add_task(research_service.perform_research, db, research)

    return research


@router.post("/property/{property_id}/market-analysis", response_model=ResearchResponse)
async def market_analysis(
    property_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Quick endpoint to run market analysis.

    Analyzes:
    1. Comparable properties
    2. Price trends
    3. Price per square foot
    4. Market positioning
    """
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    research = Research(
        research_type=ResearchType.MARKET_ANALYSIS,
        property_id=property_id,
        status=ResearchStatus.PENDING
    )
    db.add(research)
    db.commit()
    db.refresh(research)

    background_tasks.add_task(research_service.perform_research, db, research)

    return research


@router.post("/property/{property_id}/compliance", response_model=ResearchResponse)
async def compliance_research(
    property_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Quick endpoint to run comprehensive compliance check.

    Validates:
    1. Legal compliance
    2. Contract compliance
    3. Generates remediation plan
    """
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    research = Research(
        research_type=ResearchType.COMPLIANCE_CHECK,
        property_id=property_id,
        status=ResearchStatus.PENDING
    )
    db.add(research)
    db.commit()
    db.refresh(research)

    background_tasks.add_task(research_service.perform_research, db, research)

    return research


@router.get("/property/{property_id}/latest", response_model=ResearchResponse)
def get_latest_research(property_id: int, db: Session = Depends(get_db)):
    """
    Get the most recent completed research for a property.

    Useful for getting cached research results without re-running.
    """
    research = db.query(Research).filter(
        Research.property_id == property_id,
        Research.status == ResearchStatus.COMPLETED
    ).order_by(Research.completed_at.desc()).first()

    if not research:
        raise HTTPException(
            status_code=404,
            detail="No completed research found for this property"
        )

    return research


# ========== Custom Research Types ==========

@router.post("/ai-research", response_model=ResearchResponse)
async def create_ai_research(
    request: AIResearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create custom AI research with configurable prompts and models.

    This endpoint allows you to ask any question or perform custom analysis
    using Claude AI with full control over the prompt and model parameters.

    Example:
    {
        "property_id": 1,
        "prompt": "What are the top 5 risks I should be aware of for this property?",
        "model": "claude-3-5-sonnet-20241022",
        "temperature": 0.7,
        "property_context": true
    }

    Available models:
    - claude-3-5-sonnet-20241022 (recommended, latest)
    - claude-3-5-haiku-20241022 (fastest)
    - claude-3-opus-20240229 (most capable)
    - claude-3-haiku-20240307 (legacy)
    """
    # Validate property if provided
    if request.property_id:
        property = db.query(Property).filter(Property.id == request.property_id).first()
        if not property:
            raise HTTPException(status_code=404, detail="Property not found")

    # Create research job
    research = Research(
        research_type=ResearchType.AI_RESEARCH,
        property_id=request.property_id,
        parameters={
            "prompt": request.prompt,
            "model": request.model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "system_prompt": request.system_prompt,
            "property_context": request.property_context
        },
        status=ResearchStatus.PENDING
    )
    db.add(research)
    db.commit()
    db.refresh(research)

    # Start research in background
    background_tasks.add_task(research_service.perform_research, db, research)

    return research


@router.post("/api-research", response_model=ResearchResponse)
async def create_api_research(
    request: APIResearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create custom API research to call external services.

    This endpoint allows you to orchestrate multiple API calls to external
    services and aggregate the results. Useful for integrating third-party
    data sources like skip tracing, property data APIs, etc.

    Example:
    {
        "property_id": 1,
        "endpoints": [
            {
                "name": "Get weather data",
                "url": "https://api.weather.com/data",
                "method": "GET",
                "headers": {"Authorization": "Bearer token"},
                "params": {"location": "Dallas, TX"}
            },
            {
                "name": "Get crime stats",
                "url": "https://api.crime.com/stats",
                "method": "POST",
                "json": {"address": "123 Main St", "radius": 1}
            }
        ]
    }
    """
    # Validate property if provided
    if request.property_id:
        property = db.query(Property).filter(Property.id == request.property_id).first()
        if not property:
            raise HTTPException(status_code=404, detail="Property not found")

    # Create research job
    research = Research(
        research_type=ResearchType.API_RESEARCH,
        property_id=request.property_id,
        parameters={
            "endpoints": [endpoint.model_dump(by_alias=True) for endpoint in request.endpoints]
        },
        status=ResearchStatus.PENDING
    )
    db.add(research)
    db.commit()
    db.refresh(research)

    # Start research in background
    background_tasks.add_task(research_service.perform_research, db, research)

    return research
