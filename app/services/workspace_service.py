"""Workspace service for multi-tenant SaaS support."""

import logging
import secrets
from typing import Optional, List
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.models.workspace import Workspace, WorkspaceAPIKey, CommandPermission, API_SCOPES

logger = logging.getLogger(__name__)

# Password hashing for API keys
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class WorkspaceService:
    """Service for managing workspaces and multi-tenant isolation."""

    @staticmethod
    def create_workspace(
        db: Session,
        name: str,
        owner_email: str,
        owner_name: str,
        subscription_tier: str = "free"
    ) -> Workspace:
        """Create a new workspace.

        Args:
            db: Database session
            name: Workspace name (e.g., "Acme Realty")
            owner_email: Owner's email
            owner_name: Owner's full name
            subscription_tier: free, pro, or enterprise

        Returns:
            Created workspace with initial API key
        """
        # Generate initial API key
        api_key = f"air_{secrets.token_urlsafe(32)}"
        api_key_hash = pwd_context.hash(api_key)

        # Create workspace
        workspace = Workspace(
            name=name,
            owner_email=owner_email,
            owner_name=owner_name,
            api_key_hash=api_key_hash,
            subscription_tier=subscription_tier,
            max_agents=1 if subscription_tier == "free" else 10,
            max_properties=50 if subscription_tier == "free" else 1000,
            settings={
                "features": {
                    "hybrid_search": True,
                    "market_intelligence": subscription_tier != "free",
                    "predictive_analytics": subscription_tier in ["pro", "enterprise"],
                    "white_label": subscription_tier == "enterprise"
                }
            }
        )

        db.add(workspace)
        db.flush()  # Get workspace ID

        # Create initial API key with full scopes
        initial_key = WorkspaceAPIKey(
            workspace_id=workspace.id,
            name="Initial Admin Key",
            key_hash=api_key_hash,
            key_prefix=api_key[:10],
            scopes=list(API_SCOPES.keys())  # Full access
        )

        db.add(initial_key)
        db.commit()
        db.refresh(workspace)

        logger.info(f"Created workspace '{name}' (ID: {workspace.id})")

        # Return workspace with API key (only time it's shown!)
        workspace.initial_api_key = api_key

        return workspace

    @staticmethod
    def get_workspace_by_api_key(db: Session, api_key: str) -> Optional[Workspace]:
        """Get workspace by API key.

        Args:
            db: Database session
            api_key: API key from request header

        Returns:
            Workspace if valid, None otherwise
        """
        # Hash the provided key
        api_key_hash = pwd_context.hash(api_key)

        # Note: bcrypt hash includes salt, so we can't do exact match
        # Instead, we get all active workspaces and verify
        workspaces = db.query(Workspace).filter(
            Workspace.is_active == True,
            Workspace.deleted_at.is_(None)
        ).all()

        for workspace in workspaces:
            if pwd_context.verify(api_key, workspace.api_key_hash):
                # Also check API keys table for workspace-specific keys
                ws_api_keys = db.query(WorkspaceAPIKey).filter(
                    WorkspaceAPIKey.workspace_id == workspace.id
                ).all()

                for key in ws_api_keys:
                    if key.is_valid and pwd_context.verify(api_key, key.key_hash):
                        # Update last used
                        key.last_used_at = datetime.now(timezone.utc)
                        key.usage_count += 1
                        db.commit()

                        return workspace

        return None

    @staticmethod
    def create_api_key(
        db: Session,
        workspace_id: int,
        name: str,
        scopes: List[str],
        agent_id: Optional[int] = None,
        expires_days: Optional[int] = None
    ) -> tuple[str, WorkspaceAPIKey]:
        """Create a new API key for a workspace.

        Args:
            db: Database session
            workspace_id: Workspace ID
            name: Key name (e.g., "Dashboard Read-Only")
            scopes: List of permitted scopes
            agent_id: Optional agent ID (NULL = workspace-level key)
            expires_days: Optional expiration in days

        Returns:
            (api_key, api_key_object) - API key is only shown once!
        """
        # Generate secure key
        api_key = f"air_{secrets.token_urlsafe(32)}"
        api_key_hash = pwd_context.hash(api_key)
        key_prefix = api_key[:10]

        # Calculate expiration
        expires_at = None
        if expires_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)

        # Create API key
        api_key_obj = WorkspaceAPIKey(
            workspace_id=workspace_id,
            agent_id=agent_id,
            name=name,
            key_hash=api_key_hash,
            key_prefix=key_prefix,
            scopes=scopes,
            expires_at=expires_at
        )

        db.add(api_key_obj)
        db.commit()
        db.refresh(api_key_obj)

        logger.info(f"Created API key '{name}' for workspace {workspace_id}")

        return api_key, api_key_obj

    @staticmethod
    def list_api_keys(db: Session, workspace_id: int) -> List[dict]:
        """List all API keys for a workspace.

        Args:
            db: Database session
            workspace_id: Workspace ID

        Returns:
            List of API key info (never shows full key!)
        """
        keys = db.query(WorkspaceAPIKey).filter(
            WorkspaceAPIKey.workspace_id == workspace_id
        ).order_by(WorkspaceAPIKey.created_at.desc()).all()

        return [
            {
                "id": k.id,
                "name": k.name,
                "key_prefix": k.key_prefix,
                "scopes": k.scopes,
                "agent_id": k.agent_id,
                "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
                "usage_count": k.usage_count,
                "expires_at": k.expires_at.isoformat() if k.expires_at else None,
                "is_valid": k.is_valid,
                "created_at": k.created_at.isoformat()
            }
            for k in keys
        ]

    @staticmethod
    def revoke_api_key(db: Session, api_key_id: int) -> bool:
        """Revoke an API key.

        Args:
            db: Database session
            api_key_id: API key ID

        Returns:
            True if revoked, False if not found
        """
        key = db.query(WorkspaceAPIKey).filter(
            WorkspaceAPIKey.id == api_key_id
        ).first()

        if not key:
            return False

        key.revoked_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(f"Revoked API key '{key.name}' (ID: {api_key_id})")

        return True

    @staticmethod
    def set_command_permission(
        db: Session,
        workspace_id: int,
        command_pattern: str,
        permission: str,
        agent_id: Optional[int] = None,
        reason: Optional[str] = None
    ) -> CommandPermission:
        """Set a command permission rule.

        Args:
            db: Database session
            workspace_id: Workspace ID
            command_pattern: Command pattern (e.g., "delete_*", "properties.delete")
            permission: allow, deny, or require_approval
            agent_id: Optional agent ID (NULL = applies to all agents)
            reason: Optional reason for this permission

        Returns:
            Created permission
        """
        perm = CommandPermission(
            workspace_id=workspace_id,
            agent_id=agent_id,
            command_pattern=command_pattern,
            permission=permission,
            reason=reason
        )

        db.add(perm)
        db.commit()
        db.refresh(perm)

        logger.info(
            f"Set permission '{permission}' for pattern '{command_pattern}' "
            f"in workspace {workspace_id}"
        )

        return perm

    @staticmethod
    def check_command_permission(
        db: Session,
        workspace_id: int,
        agent_id: int,
        command: str
    ) -> tuple[bool, Optional[str]]:
        """Check if an agent can execute a command.

        Args:
            db: Database session
            workspace_id: Workspace ID
            agent_id: Agent ID
            command: Command to check

        Returns:
            (allowed, reason) - allowed=False means denied or requires approval
        """
        # 1. Check workspace-wide permissions (agent_id is NULL)
        workspace_perms = db.query(CommandPermission).filter(
            CommandPermission.workspace_id == workspace_id,
            CommandPermission.agent_id.is_(None)
        ).all()

        for perm in workspace_perms:
            if WorkspaceService._matches_pattern(command, perm.command_pattern):
                if perm.permission == "deny":
                    return False, f"Command '{command}' is denied by workspace policy: {perm.reason or 'No reason provided'}"
                elif perm.permission == "require_approval":
                    return False, f"Command '{command}' requires approval from workspace owner"

        # 2. Check agent-specific permissions
        agent_perms = db.query(CommandPermission).filter(
            CommandPermission.workspace_id == workspace_id,
            CommandPermission.agent_id == agent_id
        ).all()

        for perm in agent_perms:
            if WorkspaceService._matches_pattern(command, perm.command_pattern):
                if perm.permission == "deny":
                    return False, f"Command '{command}' is denied for this agent: {perm.reason or 'No reason provided'}"
                elif perm.permission == "require_approval":
                    return False, f"Command '{command}' requires approval"

        # 3. Default: allow
        return True, None

    @staticmethod
    def _matches_pattern(command: str, pattern: str) -> bool:
        """Check if command matches a pattern.

        Supports:
        - Exact match: "delete_property"
        - Wildcard prefix: "delete_*"
        - Wildcard suffix: "properties.*"

        Args:
            command: Command to check
            pattern: Pattern to match against

        Returns:
            True if command matches pattern
        """
        if pattern == "*":
            return True

        if pattern == command:
            return True

        # Wildcard prefix: "delete_*"
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return command.startswith(prefix)

        # Wildcard suffix: "properties.*"
        if pattern.startswith("*"):
            suffix = pattern[1:]
            return command.endswith(suffix)

        # Contains wildcard: "properties_*_delete"
        if "*" in pattern:
            parts = pattern.split("*")
            if len(parts) == 2:
                return command.startswith(parts[0]) and command.endswith(parts[1])

        return False

    @staticmethod
    def get_workspace_stats(db: Session, workspace_id: int) -> dict:
        """Get usage statistics for a workspace.

        Args:
            db: Database session
            workspace_id: Workspace ID

        Returns:
            Usage statistics
        """
        from app.models.property import Property
        from app.models.agent import Agent
        from app.models.contact import Contact

        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace:
            return {}

        # Count resources
        agent_count = db.query(Agent).filter(Agent.workspace_id == workspace_id).count()
        property_count = db.query(Property).filter(Property.workspace_id == workspace_id).count()
        contact_count = db.query(Contact).filter(Contact.workspace_id == workspace_id).count()

        # Count API keys
        api_key_count = db.query(WorkspaceAPIKey).filter(
            WorkspaceAPIKey.workspace_id == workspace_id,
            WorkspaceAPIKey.revoked_at.is_(None)
        ).count()

        # Calculate usage percentage
        agent_usage = (agent_count / workspace.max_agents * 100) if workspace.max_agents > 0 else 0
        property_usage = (property_count / workspace.max_properties * 100) if workspace.max_properties > 0 else 0

        return {
            "workspace_id": workspace_id,
            "subscription_tier": workspace.subscription_tier,
            "created_at": workspace.created_at.isoformat(),
            "usage": {
                "agents": {
                    "current": agent_count,
                    "max": workspace.max_agents,
                    "usage_percent": round(agent_usage, 1)
                },
                "properties": {
                    "current": property_count,
                    "max": workspace.max_properties,
                    "usage_percent": round(property_usage, 1)
                },
                "contacts": {
                    "current": contact_count
                },
                "api_keys": {
                    "current": api_key_count
                }
            }
        }


# Global service instance
workspace_service = WorkspaceService()
