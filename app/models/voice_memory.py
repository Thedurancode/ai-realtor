from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

from app.database import Base


class VoiceMemoryNode(Base):
    """Persistent memory node for voice sessions."""

    __tablename__ = "voice_memory_nodes"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(128), nullable=False, index=True)
    node_type = Column(String(64), nullable=False, index=True)
    node_key = Column(String(255), nullable=False, index=True)
    summary = Column(String(512), nullable=True)
    payload = Column(JSON, nullable=True)
    importance = Column(Float, nullable=False, default=0.5)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    outgoing_edges = relationship(
        "VoiceMemoryEdge",
        back_populates="source_node",
        foreign_keys="VoiceMemoryEdge.source_node_id",
        cascade="all, delete-orphan",
    )
    incoming_edges = relationship(
        "VoiceMemoryEdge",
        back_populates="target_node",
        foreign_keys="VoiceMemoryEdge.target_node_id",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("session_id", "node_type", "node_key", name="uq_voice_memory_node"),
        Index("ix_voice_memory_nodes_session_type", "session_id", "node_type"),
    )


class VoiceMemoryEdge(Base):
    """Directed relationship between voice memory nodes."""

    __tablename__ = "voice_memory_edges"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(128), nullable=False, index=True)
    source_node_id = Column(Integer, ForeignKey("voice_memory_nodes.id", ondelete="CASCADE"), nullable=False)
    target_node_id = Column(Integer, ForeignKey("voice_memory_nodes.id", ondelete="CASCADE"), nullable=False)
    relation = Column(String(64), nullable=False, index=True)
    weight = Column(Float, nullable=False, default=1.0)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    source_node = relationship("VoiceMemoryNode", foreign_keys=[source_node_id], back_populates="outgoing_edges")
    target_node = relationship("VoiceMemoryNode", foreign_keys=[target_node_id], back_populates="incoming_edges")

    __table_args__ = (
        UniqueConstraint("session_id", "source_node_id", "target_node_id", "relation", name="uq_voice_memory_edge"),
        Index("ix_voice_memory_edges_session_relation", "session_id", "relation"),
    )
