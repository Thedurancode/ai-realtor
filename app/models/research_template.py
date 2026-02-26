"""
Research Template Model

Pre-configured AI agent templates for research workflows.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Enum
from sqlalchemy.sql import func
import enum

from app.database import Base
from app.models.research import ResearchType


class TemplateCategory(str, enum.Enum):
    """Categories for organizing research templates"""
    PROPERTY_ANALYSIS = "property_analysis"
    MARKET_RESEARCH = "market_research"
    INVESTMENT_ANALYSIS = "investment_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    DUE_DILIGENCE = "due_diligence"
    CUSTOM = "custom"


class ResearchTemplate(Base):
    """
    Pre-configured research agent templates.

    Templates act like AI agents - they have a specific purpose,
    personality, and set of instructions that can be triggered with one click.

    Examples:
    - "Investment Risk Analyzer" - Analyzes all investment risks for a property
    - "Market Comparables Expert" - Deep dive into comparable properties
    - "Due Diligence Specialist" - Complete due diligence checklist
    - "Contract Compliance Auditor" - Reviews all contract requirements
    """
    __tablename__ = "research_templates"

    id = Column(Integer, primary_key=True, index=True)

    # Template identification
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(Enum(TemplateCategory), default=TemplateCategory.CUSTOM, index=True)
    icon = Column(String(50), nullable=True)  # Emoji or icon identifier

    # Research configuration
    research_type = Column(Enum(ResearchType), nullable=False)

    # For AI_RESEARCH templates
    ai_prompt_template = Column(Text, nullable=True)  # Prompt with {property.address} placeholders
    ai_system_prompt = Column(Text, nullable=True)  # System prompt defining the agent's personality
    ai_model = Column(String(100), nullable=True)  # Default model to use
    ai_temperature = Column(String(10), nullable=True)  # 0.0 - 1.0
    ai_max_tokens = Column(Integer, nullable=True)

    # For API_RESEARCH templates
    api_endpoints = Column(JSON, nullable=True)  # List of API endpoints to call

    # For built-in research types (PROPERTY_ANALYSIS, MARKET_ANALYSIS, etc.)
    research_parameters = Column(JSON, nullable=True)  # Additional parameters

    # Template metadata
    is_system_template = Column(Boolean, default=False)  # System templates can't be deleted
    is_active = Column(Boolean, default=True, index=True)
    execution_count = Column(Integer, default=0)  # Track popularity

    # Agent personality (for display)
    agent_name = Column(String(100), nullable=True)  # "Dr. Risk", "Market Maven", etc.
    agent_expertise = Column(Text, nullable=True)  # What this agent specializes in

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_research_params(self, property_id: int = None) -> dict:
        """Convert template to research parameters"""
        params = {}

        if self.research_type == ResearchType.AI_RESEARCH:
            params = {
                "prompt": self.ai_prompt_template,
                "model": self.ai_model or "claude-3-5-sonnet-20241022",
                "temperature": float(self.ai_temperature) if self.ai_temperature else 1.0,
                "max_tokens": self.ai_max_tokens or 4096,
                "system_prompt": self.ai_system_prompt,
                "property_context": True
            }
        elif self.research_type == ResearchType.API_RESEARCH:
            params = {
                "endpoints": self.api_endpoints or []
            }
        else:
            params = self.research_parameters or {}

        return params
