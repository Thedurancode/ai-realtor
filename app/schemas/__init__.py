from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse
from app.schemas.property import PropertyCreate, PropertyUpdate, PropertyResponse
from app.schemas.contract import ContractCreate, ContractUpdate, ContractResponse
from app.schemas.notification import NotificationCreate, NotificationResponse
from app.schemas.activity import ActivityEventCreate, ActivityEventUpdate, ActivityEventResponse
from app.schemas.property_recap import RecapResponse, PhoneCallRequest, PhoneCallResponse
from app.schemas.agent_conversation import (
    AgentExecuteRequest,
    AgentFromTemplateRequest,
    AgentConversationResponse,
    VoiceGoalExecuteRequest,
    VoiceGoalExecuteResponse,
    VoiceMemoryEventRequest,
)
from app.schemas.research import ResearchCreateRequest, ResearchResponse, AIResearchRequest, APIResearchRequest
from app.schemas.research_template import ResearchTemplateCreate, ResearchTemplateUpdate, ResearchTemplateResponse
from app.schemas.agentic_research import ResearchInput, AgenticJobCreateResponse, AgenticJobStatusResponse, PropertyEnvelope, DossierEnvelope

__all__ = [
    "AgentCreate",
    "AgentUpdate",
    "AgentResponse",
    "PropertyCreate",
    "PropertyUpdate",
    "PropertyResponse",
    "ContractCreate",
    "ContractUpdate",
    "ContractResponse",
    "NotificationCreate",
    "NotificationResponse",
    "ActivityEventCreate",
    "ActivityEventUpdate",
    "ActivityEventResponse",
    "RecapResponse",
    "PhoneCallRequest",
    "PhoneCallResponse",
    "AgentExecuteRequest",
    "AgentFromTemplateRequest",
    "AgentConversationResponse",
    "VoiceGoalExecuteRequest",
    "VoiceGoalExecuteResponse",
    "VoiceMemoryEventRequest",
    "ResearchCreateRequest",
    "ResearchResponse",
    "AIResearchRequest",
    "APIResearchRequest",
    "ResearchTemplateCreate",
    "ResearchTemplateUpdate",
    "ResearchTemplateResponse",
    "ResearchInput",
    "AgenticJobCreateResponse",
    "AgenticJobStatusResponse",
    "PropertyEnvelope",
    "DossierEnvelope",
]
