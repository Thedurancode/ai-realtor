from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime as dt

from app.models.research_template import TemplateCategory
from app.models.research import ResearchType


class ResearchTemplateCreate(BaseModel):
    """Request to create a research template"""
    name: str
    description: Optional[str] = None
    category: TemplateCategory = TemplateCategory.CUSTOM
    icon: Optional[str] = None
    research_type: ResearchType
    ai_prompt_template: Optional[str] = None
    ai_system_prompt: Optional[str] = None
    ai_model: Optional[str] = "claude-3-5-sonnet-20241022"
    ai_temperature: Optional[str] = "1.0"
    ai_max_tokens: Optional[int] = 4096
    api_endpoints: Optional[List[dict]] = None
    research_parameters: Optional[dict] = None
    agent_name: Optional[str] = None
    agent_expertise: Optional[str] = None


class ResearchTemplateUpdate(BaseModel):
    """Request to update a research template"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[TemplateCategory] = None
    icon: Optional[str] = None
    ai_prompt_template: Optional[str] = None
    ai_system_prompt: Optional[str] = None
    ai_model: Optional[str] = None
    ai_temperature: Optional[str] = None
    ai_max_tokens: Optional[int] = None
    api_endpoints: Optional[List[dict]] = None
    research_parameters: Optional[dict] = None
    agent_name: Optional[str] = None
    agent_expertise: Optional[str] = None
    is_active: Optional[bool] = None


class ResearchTemplateResponse(BaseModel):
    """Research template response"""
    id: int
    name: str
    description: Optional[str]
    category: TemplateCategory
    icon: Optional[str]
    research_type: ResearchType
    ai_prompt_template: Optional[str]
    ai_system_prompt: Optional[str]
    ai_model: Optional[str]
    ai_temperature: Optional[str]
    ai_max_tokens: Optional[int]
    api_endpoints: Optional[List[dict]]
    research_parameters: Optional[dict]
    agent_name: Optional[str]
    agent_expertise: Optional[str]
    is_system_template: bool
    is_active: bool
    execution_count: int
    created_at: dt

    class Config:
        from_attributes = True


class ExecuteTemplateRequest(BaseModel):
    """Request to execute a research template"""
    property_id: Optional[int] = None
    template_variables: Optional[dict] = None
