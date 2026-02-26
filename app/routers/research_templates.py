"""
Research Templates Router

Manage AI agent templates for research workflows.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app.models.research_template import ResearchTemplate, TemplateCategory
from app.models.research import Research, ResearchStatus, ResearchType
from app.models.property import Property
from app.services.research_service import research_service
from app.schemas.research_template import ResearchTemplateCreate, ResearchTemplateUpdate, ResearchTemplateResponse, ExecuteTemplateRequest


router = APIRouter(prefix="/research-templates", tags=["research-templates"])


# ========== Endpoints ==========

@router.post("/", response_model=ResearchTemplateResponse, status_code=201)
def create_template(
    request: ResearchTemplateCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new research template (AI agent).

    Example AI Research Agent:
    {
        "name": "Investment Risk Analyzer",
        "description": "Analyzes all investment risks for a property",
        "category": "risk_assessment",
        "icon": "🔍",
        "research_type": "ai_research",
        "ai_prompt_template": "Analyze the investment risks for {property.address}. Consider market conditions, property condition, location, and financial factors.",
        "ai_system_prompt": "You are Dr. Risk, a real estate investment risk analyst with 20 years of experience. Your responses are thorough, data-driven, and highlight both opportunities and red flags.",
        "ai_model": "claude-3-5-sonnet-20241022",
        "ai_temperature": "0.3",
        "agent_name": "Dr. Risk",
        "agent_expertise": "Investment risk analysis, market trends, financial modeling"
    }
    """
    template = ResearchTemplate(
        name=request.name,
        description=request.description,
        category=request.category,
        icon=request.icon,
        research_type=request.research_type,
        ai_prompt_template=request.ai_prompt_template,
        ai_system_prompt=request.ai_system_prompt,
        ai_model=request.ai_model,
        ai_temperature=request.ai_temperature,
        ai_max_tokens=request.ai_max_tokens,
        api_endpoints=request.api_endpoints,
        research_parameters=request.research_parameters,
        agent_name=request.agent_name,
        agent_expertise=request.agent_expertise
    )

    db.add(template)
    db.commit()
    db.refresh(template)

    return template


@router.get("/", response_model=List[ResearchTemplateResponse])
def list_templates(
    category: Optional[TemplateCategory] = None,
    research_type: Optional[ResearchType] = None,
    is_active: Optional[bool] = True,
    db: Session = Depends(get_db)
):
    """
    List all research templates (AI agents).

    Filter by:
    - category: Filter by template category
    - research_type: Filter by research type
    - is_active: Show only active templates (default: true)
    """
    query = db.query(ResearchTemplate)

    if category:
        query = query.filter(ResearchTemplate.category == category)
    if research_type:
        query = query.filter(ResearchTemplate.research_type == research_type)
    if is_active is not None:
        query = query.filter(ResearchTemplate.is_active == is_active)

    return query.order_by(ResearchTemplate.execution_count.desc(), ResearchTemplate.name).all()


@router.get("/{template_id}", response_model=ResearchTemplateResponse)
def get_template(template_id: int, db: Session = Depends(get_db)):
    """Get a specific research template by ID"""
    template = db.query(ResearchTemplate).filter(ResearchTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Research template not found")

    return template


@router.patch("/{template_id}", response_model=ResearchTemplateResponse)
def update_template(
    template_id: int,
    request: ResearchTemplateUpdate,
    db: Session = Depends(get_db)
):
    """Update a research template"""
    template = db.query(ResearchTemplate).filter(ResearchTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Research template not found")

    if template.is_system_template:
        raise HTTPException(status_code=403, detail="Cannot modify system templates")

    # Update fields
    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)

    db.commit()
    db.refresh(template)

    return template


@router.delete("/{template_id}", status_code=204)
def delete_template(template_id: int, db: Session = Depends(get_db)):
    """Delete a research template"""
    template = db.query(ResearchTemplate).filter(ResearchTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Research template not found")

    if template.is_system_template:
        raise HTTPException(status_code=403, detail="Cannot delete system templates")

    db.delete(template)
    db.commit()


# ========== Execute Template ==========

from app.schemas.research import ResearchResponse

@router.post("/{template_id}/execute", response_model=ResearchResponse)
async def execute_template(
    template_id: int,
    request: ExecuteTemplateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Execute a research template (run the AI agent).

    This creates a research job from the template and starts it in the background.

    Example:
    POST /research-templates/1/execute
    {
        "property_id": 123,
        "template_variables": {
            "custom_instruction": "Focus on environmental risks"
        }
    }
    """
    template = db.query(ResearchTemplate).filter(ResearchTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Research template not found")

    if not template.is_active:
        raise HTTPException(status_code=400, detail="Template is not active")

    # Validate property if provided
    if request.property_id:
        property = db.query(Property).filter(Property.id == request.property_id).first()
        if not property:
            raise HTTPException(status_code=404, detail="Property not found")

    # Get base parameters from template
    params = template.to_research_params(request.property_id)

    # Replace template variables in prompt if applicable
    if template.research_type == ResearchType.AI_RESEARCH and request.template_variables:
        prompt = params.get("prompt", "")
        for key, value in request.template_variables.items():
            prompt = prompt.replace(f"{{{key}}}", str(value))
        params["prompt"] = prompt

    # Merge with any additional variables
    if request.template_variables and template.research_type != ResearchType.AI_RESEARCH:
        params.update(request.template_variables)

    # Create research job
    research = Research(
        research_type=template.research_type,
        property_id=request.property_id,
        parameters=params,
        status=ResearchStatus.PENDING
    )
    db.add(research)

    # Increment execution count
    template.execution_count += 1

    db.commit()
    db.refresh(research)

    # Start research in background
    background_tasks.add_task(research_service.perform_research, db, research)

    return research


@router.get("/categories/list", response_model=List[str])
def list_categories():
    """Get all available template categories"""
    return [category.value for category in TemplateCategory]
