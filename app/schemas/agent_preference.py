from pydantic import BaseModel
from datetime import datetime


class AgentPreferenceBase(BaseModel):
    key: str
    value: str
    description: str | None = None
    is_active: bool = True


class AgentPreferenceCreate(AgentPreferenceBase):
    agent_id: int


class AgentPreferenceUpdate(BaseModel):
    key: str | None = None
    value: str | None = None
    description: str | None = None
    is_active: bool | None = None


class AgentPreferenceResponse(AgentPreferenceBase):
    id: int
    agent_id: int
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class AgentContextResponse(BaseModel):
    """
    Returns all active agent preferences as a formatted context for the AI.
    This is what the AI assistant will use to understand the agent's rules.
    """
    agent_id: int
    context: str  # Formatted string of all preferences
    preferences: list[AgentPreferenceResponse]
