"""Command guard for security and access control.

Prevents unauthorized or dangerous command execution.
"""

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.services.workspace_service import workspace_service

logger = logging.getLogger(__name__)


class CommandGuard:
    """Validate and filter commands before execution."""

    # Dangerous commands that require confirmation
    DANGEROUS_COMMANDS = {
        "delete_property",
        "delete_contact",
        "delete_contract",
        "cancel_all_campaigns",
        "clear_conversation_history",
        "send_bulk_notifications",
        "delete_workspace",
        "remove_all_agents",
        "batch_delete_properties",
    }

    # Commands that require admin scope
    ADMIN_ONLY_COMMANDS = {
        "delete_workspace",
        "modify_workspace_settings",
        "manage_subscription",
        "manage_api_keys_admin",
        "workspace_administration",
    }

    def __init__(self, db: Session, workspace_id: int, agent_id: int, api_key_scopes: List[str]):
        """Initialize command guard.

        Args:
            db: Database session
            workspace_id: Workspace ID
            agent_id: Agent ID
            api_key_scopes: List of scopes from API key
        """
        self.db = db
        self.workspace_id = workspace_id
        self.agent_id = agent_id
        self.api_key_scopes = api_key_scopes

    def can_execute(self, command: str, params: dict) -> tuple[bool, str]:
        """Check if agent can execute command.

        Args:
            command: Command name
            params: Command parameters

        Returns:
            (allowed, reason) - allowed=False means denied or requires approval
        """
        # 1. Check API key scopes first
        scope_allowed, scope_reason = self._check_scope(command)
        if not scope_allowed:
            return False, scope_reason

        # 2. Check workspace/agent permissions
        perm_allowed, perm_reason = workspace_service.check_command_permission(
            self.db, self.workspace_id, self.agent_id, command
        )

        if not perm_allowed:
            return False, perm_reason

        # 3. Special validation for dangerous commands
        if command in self.DANGEROUS_COMMANDS:
            if not params.get("confirmed"):
                return False, f"Command '{command}' requires confirmation. Add confirmed=true to parameters."

            # Extra check for delete commands
            if "delete" in command.lower():
                # Check if bulk delete
                if params.get("bulk") or params.get("all"):
                    return False, "Bulk delete operations require workspace owner approval"

        # 4. Admin-only commands
        if command in self.ADMIN_ONLY_COMMANDS:
            if "admin:workspace" not in self.api_key_scopes:
                return False, f"Command '{command}' requires admin workspace scope"

        # 5. All checks passed
        return True, "OK"

    def _check_scope(self, command: str) -> tuple[bool, str]:
        """Check if API key has required scope for command.

        Args:
            command: Command to check

        Returns:
            (allowed, reason)
        """
        # Map commands to required scopes
        required_scope = self._get_required_scope(command)

        if not required_scope:
            # No scope required
            return True, None

        if "admin:*" in self.api_key_scopes or required_scope in self.api_key_scopes:
            return True, None

        # Check for wildcard scopes (read:*, write:*, etc.)
        for scope in self.api_key_scopes:
            if scope.endswith("*"):
                prefix = scope[:-1]
                if required_scope.startswith(prefix):
                    return True, None

        return False, f"Missing required scope: {required_scope}"

    def _get_required_scope(self, command: str) -> Optional[str]:
        """Get required scope for a command.

        Args:
            command: Command name

        Returns:
            Required scope or None if no scope required
        """
        # Property commands
        if command.startswith("get_property") or command.startswith("list_properties"):
            return "read:properties"
        if command.startswith("create_property") or command.startswith("update_property"):
            return "write:properties"
        if command.startswith("delete_property"):
            return "delete:properties"

        # Contact commands
        if command.startswith("get_contact") or command.startswith("list_contacts"):
            return "read:contacts"
        if command.startswith("add_contact") or command.startswith("update_contact"):
            return "write:contacts"
        if command.startswith("delete_contact"):
            return "delete:contacts"

        # Contract commands
        if command.startswith("get_contract") or command.startswith("list_contracts"):
            return "read:contracts"
        if command.startswith("create_contract") or command.startswith("send_contract"):
            return "write:contracts"
        if command.startswith("delete_contract"):
            return "delete:contracts"

        # Campaign commands
        if command.startswith("get_campaign") or command.startswith("list_campaigns"):
            return "read:campaigns"
        if command.startswith("create_campaign") or command.startswith("start_campaign"):
            return "write:campaigns"
        if command.startswith("delete_campaign") or command.startswith("cancel_campaign"):
            return "delete:campaigns"

        # Notification commands
        if command.startswith("list_notifications"):
            return "read:notifications"
        if command.startswith("send_notification") or command.startswith("create_notification"):
            return "write:notifications"

        # Analytics commands
        if command.startswith("get_analytics") or command.startswith("get_portfolio"):
            return "read:analytics"

        # Admin commands
        if "workspace" in command and "delete" in command:
            return "admin:workspace"
        if "api_key" in command and ("create" in command or "delete" in command):
            return "admin:api_keys"
        if "agent" in command and ("delete" in command or "remove" in command):
            return "admin:agents"

        # Default: no scope required
        return None


class CommandLogger:
    """Log all command executions for audit trail."""

    @staticmethod
    def log_execution(
        db: Session,
        workspace_id: int,
        agent_id: int,
        command: str,
        params: dict,
        allowed: bool,
        reason: Optional[str] = None,
        result: Optional[dict] = None
    ):
        """Log command execution.

        Args:
            db: Database session
            workspace_id: Workspace ID
            agent_id: Agent ID
            command: Command name
            params: Command parameters (sanitized)
            allowed: Whether command was allowed
            reason: Reason if denied
            result: Command result if allowed
        """
        # In production, this would write to a command_log table
        # For now, just log to Python logger

        log_level = logging.WARNING if not allowed else logging.INFO

        logger.log(
            log_level,
            f"Command: {command} | Agent: {agent_id} | Workspace: {workspace_id} | "
            f"Allowed: {allowed} | Reason: {reason or 'N/A'}"
        )

        # TODO: Store in database for audit trail
        # from app.models.command_log import CommandLog
        # log_entry = CommandLog(
        #     workspace_id=workspace_id,
        #     agent_id=agent_id,
        #     command=command,
        #     params=params,
        #     allowed=allowed,
        #     reason=reason,
        #     result=result
        # )
        # db.add(log_entry)
        # db.commit()
