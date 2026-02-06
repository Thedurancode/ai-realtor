"""
AI Agents Router

Execute autonomous AI agents with tool use and multi-step reasoning.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime as dt

from app.database import get_db
from app.models.agent_conversation import AgentConversation, ConversationStatus
from app.models.research_template import ResearchTemplate
from app.models.property import Property
from app.services.agent_executor import AgentExecutor
from app.schemas.agent_conversation import AgentExecuteRequest, AgentFromTemplateRequest, AgentConversationResponse


router = APIRouter(prefix="/ai-agents", tags=["ai-agents"])


# ========== Background Execution ==========

async def _execute_agent_task(
    db: Session,
    conversation_id: int
):
    """Background task to execute agent"""
    conversation = db.query(AgentConversation).filter(AgentConversation.id == conversation_id).first()
    if not conversation:
        return

    try:
        # Update status
        conversation.status = ConversationStatus.RUNNING
        conversation.started_at = dt.utcnow()
        db.commit()

        # Execute agent
        executor = AgentExecutor(db)
        result = await executor.execute_agent(
            task=conversation.task,
            system_prompt=conversation.system_prompt or "You are a helpful AI assistant specializing in real estate analysis.",
            property_id=conversation.property_id,
            model=conversation.model,
            max_tokens=conversation.max_tokens,
            temperature=float(conversation.temperature)
        )

        # Update conversation with results
        conversation.status = ConversationStatus.COMPLETED if result.get("success") else ConversationStatus.FAILED
        conversation.final_response = result.get("response")
        conversation.iterations = result.get("iterations", 0)
        conversation.tool_calls_made = result.get("tool_calls_made", [])
        conversation.tool_calls_count = len(result.get("tool_calls_made", []))
        conversation.execution_trace = result.get("execution_trace", [])
        conversation.error_message = result.get("error")
        conversation.completed_at = dt.utcnow()

        db.commit()

    except Exception as e:
        conversation.status = ConversationStatus.FAILED
        conversation.error_message = str(e)
        conversation.completed_at = dt.utcnow()
        db.commit()


# ========== Endpoints ==========

@router.post("/execute", response_model=AgentConversationResponse, status_code=201)
async def execute_agent(
    request: AgentExecuteRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Execute an autonomous AI agent with tool use.

    The agent can:
    - Call multiple tools to gather information
    - Reason about the results
    - Make decisions based on data
    - Provide comprehensive analysis

    Example:
    {
        "task": "Analyze property 1 and tell me if it's a good investment. Check comps, calculate ROI, and identify any risks.",
        "property_id": 1,
        "temperature": 0.3
    }

    The agent will autonomously:
    1. Get property details
    2. Find comparable properties
    3. Calculate ROI metrics
    4. Check compliance
    5. Synthesize findings into a recommendation
    """
    # Validate property if provided
    if request.property_id:
        property = db.query(Property).filter(Property.id == request.property_id).first()
        if not property:
            raise HTTPException(status_code=404, detail="Property not found")

    # Create conversation record
    conversation = AgentConversation(
        task=request.task,
        property_id=request.property_id,
        agent_id=request.agent_id,
        model=request.model,
        system_prompt=request.system_prompt,
        temperature=str(request.temperature),
        max_tokens=request.max_tokens,
        status=ConversationStatus.PENDING
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    # Start agent execution in background
    background_tasks.add_task(_execute_agent_task, db, conversation.id)

    return conversation


@router.post("/templates/{template_id}/execute", response_model=AgentConversationResponse, status_code=201)
async def execute_agent_from_template(
    template_id: int,
    request: AgentFromTemplateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Execute an AI agent from a research template.

    This converts a simple template into a true autonomous agent with tool use.

    The agent will use the template's:
    - System prompt (personality/expertise)
    - AI model settings
    - Agent name

    But will have access to ALL tools for multi-step reasoning.

    Example:
    POST /ai-agents/templates/1/execute
    {
        "property_id": 123,
        "task_override": "Focus specifically on environmental and flood risks"
    }
    """
    template = db.query(ResearchTemplate).filter(ResearchTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if not template.is_active:
        raise HTTPException(status_code=400, detail="Template is not active")

    # Validate property if provided
    if request.property_id:
        property = db.query(Property).filter(Property.id == request.property_id).first()
        if not property:
            raise HTTPException(status_code=404, detail="Property not found")

    # Build task from template
    task = request.task_override or template.ai_prompt_template or "Analyze this property comprehensively."

    # Add additional context if provided
    if request.additional_context:
        task = f"{task}\n\nAdditional context: {request.additional_context}"

    # Create conversation record
    conversation = AgentConversation(
        template_id=template_id,
        agent_name=template.agent_name,
        task=task,
        property_id=request.property_id,
        model=template.ai_model or "claude-sonnet-4-20250514",
        system_prompt=template.ai_system_prompt,
        temperature=template.ai_temperature or "0.7",
        max_tokens=template.ai_max_tokens or 4096,
        status=ConversationStatus.PENDING
    )

    db.add(conversation)

    # Increment template execution count
    template.execution_count += 1

    db.commit()
    db.refresh(conversation)

    # Start agent execution in background
    background_tasks.add_task(_execute_agent_task, db, conversation.id)

    return conversation


@router.get("/{conversation_id}", response_model=AgentConversationResponse)
def get_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """
    Get agent conversation status and results.

    Poll this endpoint to check:
    - Status (pending, running, completed, failed)
    - Tool calls made
    - Final response
    - Execution trace (for debugging)
    """
    conversation = db.query(AgentConversation).filter(AgentConversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation


@router.get("/", response_model=List[AgentConversationResponse])
def list_conversations(
    property_id: Optional[int] = None,
    template_id: Optional[int] = None,
    status: Optional[ConversationStatus] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """List agent conversations with optional filters"""
    query = db.query(AgentConversation)

    if property_id:
        query = query.filter(AgentConversation.property_id == property_id)
    if template_id:
        query = query.filter(AgentConversation.template_id == template_id)
    if status:
        query = query.filter(AgentConversation.status == status)

    return query.order_by(AgentConversation.created_at.desc()).limit(limit).all()


@router.delete("/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """Delete an agent conversation"""
    conversation = db.query(AgentConversation).filter(AgentConversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    db.delete(conversation)
    db.commit()


# ========== Quick Access Endpoints ==========

@router.post("/property/{property_id}/analyze", response_model=AgentConversationResponse)
async def quick_property_analysis(
    property_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Quick property analysis using autonomous agent.

    The agent will automatically:
    1. Get property details
    2. Find and analyze comparables
    3. Calculate investment ROI
    4. Check compliance
    5. Provide buy/pass recommendation

    This is a convenience endpoint that creates a fully autonomous analysis.
    """
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    task = """Perform a comprehensive investment analysis on this property.

Your task:
1. Get the property details
2. Find comparable properties to assess market positioning
3. Calculate detailed ROI metrics (cash flow, cap rate, cash-on-cash return)
4. Check compliance status
5. Identify any red flags or concerns

Then provide a clear BUY or PASS recommendation with your reasoning.

Be thorough and use ALL available tools to gather complete information."""

    system_prompt = """You are a seasoned real estate investment analyst. You make data-driven decisions and never rush to judgment without gathering complete information.

Your process:
- Always start by gathering comprehensive data using your tools
- Analyze numbers conservatively
- Look for red flags
- Consider both upside and downside scenarios
- Provide clear, actionable recommendations

You have access to tools that can get property data, comparables, ROI calculations, and compliance checks. Use them all."""

    conversation = AgentConversation(
        agent_name="Investment Analyst",
        task=task,
        property_id=property_id,
        model="claude-sonnet-4-20250514",
        system_prompt=system_prompt,
        temperature="0.3",
        max_tokens=4096,
        status=ConversationStatus.PENDING
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    background_tasks.add_task(_execute_agent_task, db, conversation.id)

    return conversation
