"""
Agent Conversation Model

Stores AI agent execution history and results.
"""
from sqlalchemy import Column, Index, Integer, String, DateTime, ForeignKey, Text, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class ConversationStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentConversation(Base):
    """
    Stores the execution history of an AI agent.

    Unlike simple research jobs, agent conversations can have:
    - Multiple tool calls
    - Multi-turn reasoning
    - Self-correction
    - Iterative refinement
    """
    __tablename__ = "agent_conversations"
    __table_args__ = (
        Index("ix_agent_conversations_property_id", "property_id"),
        Index("ix_agent_conversations_agent_id", "agent_id"),
        Index("ix_agent_conversations_status", "status"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Agent configuration
    template_id = Column(Integer, ForeignKey("research_templates.id"), nullable=True)
    agent_name = Column(String(200), nullable=True)  # Friendly name (Dr. Risk, etc.)

    # Task context
    task = Column(Text, nullable=False)  # The task given to the agent
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)

    # Model configuration
    model = Column(String(100), default="claude-sonnet-4-20250514")
    system_prompt = Column(Text, nullable=True)
    temperature = Column(String(10), default="0.7")
    max_tokens = Column(Integer, default=4096)

    # Execution status
    status = Column(Enum(ConversationStatus), default=ConversationStatus.PENDING)
    iterations = Column(Integer, default=0)  # Number of agent turns
    tool_calls_count = Column(Integer, default=0)  # Total tool calls made

    # Results
    final_response = Column(Text, nullable=True)  # Agent's final answer
    tool_calls_made = Column(JSON, nullable=True)  # List of all tool calls
    execution_trace = Column(JSON, nullable=True)  # Full execution history
    error_message = Column(Text, nullable=True)

    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    property = relationship("Property", backref="agent_conversations")
    agent = relationship("Agent", backref="agent_conversations")
    template = relationship("ResearchTemplate", backref="agent_conversations")
