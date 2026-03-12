from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.agent import Agent
from app.models.agent_preference import AgentPreference
from app.schemas.agent_preference import (
    AgentPreferenceCreate,
    AgentPreferenceUpdate,
    AgentPreferenceResponse,
    AgentContextResponse,
)

router = APIRouter(prefix="/agent-preferences", tags=["agent-preferences"])


@router.post("/", response_model=AgentPreferenceResponse, status_code=201)
def create_preference(preference: AgentPreferenceCreate, db: Session = Depends(get_db)):
    """Create a new agent preference/business rule."""
    agent = db.query(Agent).filter(Agent.id == preference.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    new_preference = AgentPreference(
        agent_id=preference.agent_id,
        key=preference.key,
        value=preference.value,
        description=preference.description,
        is_active=preference.is_active,
    )
    db.add(new_preference)
    db.commit()
    db.refresh(new_preference)
    return new_preference


@router.get("/agent/{agent_id}", response_model=list[AgentPreferenceResponse])
def list_preferences_for_agent(
    agent_id: int,
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    """List all preferences for an agent."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    preferences_query = db.query(AgentPreference).filter(
        AgentPreference.agent_id == agent_id
    )

    if active_only:
        preferences_query = preferences_query.filter(AgentPreference.is_active == True)

    preferences = preferences_query.order_by(AgentPreference.created_at).all()
    return preferences


@router.get("/agent/{agent_id}/context", response_model=AgentContextResponse)
def get_agent_context(agent_id: int, db: Session = Depends(get_db)):
    """
    Get formatted context for the AI assistant.
    This endpoint returns all active preferences as a formatted string
    that can be used as system context for the AI.
    """
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    preferences = (
        db.query(AgentPreference)
        .filter(AgentPreference.agent_id == agent_id, AgentPreference.is_active == True)
        .order_by(AgentPreference.key)
        .all()
    )

    if not preferences:
        context = f"Agent: {agent.name}\nNo specific preferences or business rules set."
    else:
        context_lines = [f"Agent: {agent.name}", "\nBusiness Rules & Preferences:"]
        for pref in preferences:
            if pref.description:
                context_lines.append(f"- {pref.description}: {pref.value}")
            else:
                context_lines.append(f"- {pref.key}: {pref.value}")
        context = "\n".join(context_lines)

    return AgentContextResponse(
        agent_id=agent_id,
        context=context,
        preferences=preferences,
    )


@router.get("/{preference_id}", response_model=AgentPreferenceResponse)
def get_preference(preference_id: int, db: Session = Depends(get_db)):
    """Get a specific preference by ID."""
    preference = (
        db.query(AgentPreference).filter(AgentPreference.id == preference_id).first()
    )
    if not preference:
        raise HTTPException(status_code=404, detail="Preference not found")
    return preference


@router.patch("/{preference_id}", response_model=AgentPreferenceResponse)
def update_preference(
    preference_id: int,
    preference: AgentPreferenceUpdate,
    db: Session = Depends(get_db),
):
    """Update a preference."""
    db_preference = (
        db.query(AgentPreference).filter(AgentPreference.id == preference_id).first()
    )
    if not db_preference:
        raise HTTPException(status_code=404, detail="Preference not found")

    update_data = preference.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_preference, field, value)

    db.commit()
    db.refresh(db_preference)
    return db_preference


@router.delete("/{preference_id}", status_code=204)
def delete_preference(preference_id: int, db: Session = Depends(get_db)):
    """Delete a preference."""
    db_preference = (
        db.query(AgentPreference).filter(AgentPreference.id == preference_id).first()
    )
    if not db_preference:
        raise HTTPException(status_code=404, detail="Preference not found")

    db.delete(db_preference)
    db.commit()
    return None
