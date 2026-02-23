"""Workspace models for multi-tenant SaaS support."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Workspace(Base):
    """Isolated workspace for multi-tenant support.

    Each workspace represents a separate real estate agency or brokerage
    with complete data isolation from other workspaces.
    """
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    owner_email = Column(String(255), nullable=False, index=True)
    owner_name = Column(String(255))
    api_key_hash = Column(String(255), unique=True, nullable=False, index=True)

    # Workspace settings
    settings = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True, index=True)

    # Billing/usage tracking
    subscription_tier = Column(String(50), default="free")  # free, pro, enterprise
    max_agents = Column(Integer, default=1)
    max_properties = Column(Integer, default=50)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), index=True)  # Soft delete

    # Relationships
    agents = relationship("Agent", back_populates="workspace", cascade="all, delete-orphan")
    api_keys = relationship("WorkspaceAPIKey", back_populates="workspace", cascade="all, delete-orphan")
    command_permissions = relationship("CommandPermission", back_populates="workspace", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Workspace(id={self.id}, name='{self.name}', tier={self.subscription_tier})>"


class WorkspaceAPIKey(Base):
    """API keys with scoped permissions for workspace access control.

    Allows creating multiple keys with different permission levels:
    - Read-only keys for dashboards
    - Full access keys for mobile apps
    - Temporary keys with expiration
    """
    __tablename__ = "workspace_api_keys"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True, index=True)

    # Key identification
    name = Column(String(100), nullable=False)  # "Dashboard Key", "Mobile App Key"
    key_hash = Column(String(255), unique=True, nullable=False, index=True)
    key_prefix = Column(String(10), nullable=False)  # "air_abc1..." for display

    # Scoping (comma-separated or JSON array)
    scopes = Column(JSON, default=list)  # ["read:properties", "write:contacts"]

    # Usage tracking
    last_used_at = Column(DateTime(timezone=True))
    usage_count = Column(Integer, default=0)

    # Lifecycle
    expires_at = Column(DateTime(timezone=True), index=True)
    revoked_at = Column(DateTime(timezone=True), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    workspace = relationship("Workspace", back_populates="api_keys")

    def __repr__(self):
        return f"<WorkspaceAPIKey(id={self.id}, name='{self.name}', prefix='{self.key_prefix}')>"

    @property
    def is_valid(self) -> bool:
        """Check if API key is valid (not expired or revoked)."""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)

        if self.revoked_at:
            return False

        if self.expires_at and self.expires_at < now:
            return False

        return True


class CommandPermission(Base):
    """Control which agents can execute which commands.

    Enables workspace-level and agent-specific command filtering:
    - Workspace-wide: "No one can delete properties"
    - Agent-specific: "Junior agents cannot send bulk notifications"
    - Require approval: "Market scans require owner approval"
    """
    __tablename__ = "command_permissions"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True, index=True)  # NULL = all agents

    # Command pattern (supports wildcards: "delete_*", "properties.*")
    command_pattern = Column(String(100), nullable=False, index=True)

    # Permission level
    permission = Column(String(20), nullable=False)  # allow, deny, require_approval

    # Metadata
    reason = Column(Text)  # Why this permission exists
    created_by = Column(Integer, ForeignKey("agents.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    workspace = relationship("Workspace", back_populates="command_permissions")

    def __repr__(self):
        agent_info = f"agent {self.agent_id}" if self.agent_id else "all agents"
        return f"<CommandPermission(pattern='{self.command_pattern}', {self.permission} for {agent_info})>"


# Available permission scopes
API_SCOPES = {
    # Property scopes
    "read:properties": "Read property data",
    "write:properties": "Create and update properties",
    "delete:properties": "Delete properties",

    # Contact scopes
    "read:contacts": "Read contact data",
    "write:contacts": "Create and update contacts",
    "delete:contacts": "Delete contacts",

    # Contract scopes
    "read:contracts": "Read contract data",
    "write:contracts": "Create and update contracts",
    "delete:contracts": "Delete contracts",

    # Campaign scopes
    "read:campaigns": "Read campaign data",
    "write:campaigns": "Create and update campaigns",
    "delete:campaigns": "Delete campaigns",

    # Notification scopes
    "read:notifications": "Read notifications",
    "write:notifications": "Create and send notifications",

    # Analytics scopes
    "read:analytics": "View analytics and reports",

    # Admin scopes
    "admin:workspace": "Full workspace administration",
    "admin:api_keys": "Manage API keys",
    "admin:agents": "Manage agents in workspace",
    "admin:billing": "Manage billing and subscription",
}
