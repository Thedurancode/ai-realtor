from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime as dt

from app.models.agent_conversation import ConversationStatus


class AgentExecuteRequest(BaseModel):
    """Request to execute an AI agent"""
    task: str
    property_id: Optional[int] = None
    agent_id: Optional[int] = None
    model: Optional[str] = "claude-sonnet-4-20250514"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 4096
    system_prompt: Optional[str] = None


class AgentFromTemplateRequest(BaseModel):
    """Request to execute agent from template"""
    property_id: Optional[int] = None
    task_override: Optional[str] = None
    additional_context: Optional[str] = None


class AgentConversationResponse(BaseModel):
    """Agent conversation response"""
    id: int
    template_id: Optional[int]
    agent_name: Optional[str]
    task: str
    property_id: Optional[int]
    model: str
    status: ConversationStatus
    iterations: int
    tool_calls_count: int
    final_response: Optional[str]
    tool_calls_made: Optional[List[dict]]
    execution_trace: Optional[List[dict]]
    error_message: Optional[str]
    started_at: Optional[dt]
    completed_at: Optional[dt]
    created_at: dt

    class Config:
        from_attributes = True
