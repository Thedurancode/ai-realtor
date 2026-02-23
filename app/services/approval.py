"""Approval Manager for High-Risk Operations.

Inspired by ZeroClaw's approval system, this module provides interactive
supervision for dangerous operations with configurable auto-approve rules,
session allowlists, and comprehensive audit logging.

Usage:
    approval_manager = ApprovalManager(config={
        "level": "supervised",  # supervised, semi_auto, full_auto
        "auto_approve": ["get_property", "list_properties"],
        "always_ask": ["send_contract", "withdraw_offer", "skip_trace_property"]
    })

    # Check if operation needs approval
    if await approval_manager.requires_approval("send_contract"):
        result = await approval_manager.request_approval(
            session_id="agent-session-123",
            tool_name="send_contract",
            input_data={"property_id": 5, "contract_id": 3}
        )
        if result.granted:
            # Proceed with operation
            pass
"""

from datetime import datetime
from typing import Dict, List, Optional, Set, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json


class ApprovalRequest(BaseModel):
    """Approval request details."""
    session_id: str
    tool_name: str
    input_data: Dict[str, Any]
    timestamp: datetime
    risk_level: str  # low, medium, high, critical
    reason: Optional[str] = None


class ApprovalResult(BaseModel):
    """Result of approval request."""
    granted: bool
    reason: Optional[str] = None
    autonomy_level: str
    timestamp: datetime


class ApprovalLogEntry(BaseModel):
    """Audit log entry for approval decisions."""
    session_id: str
    tool_name: str
    granted: bool
    risk_level: str
    timestamp: datetime
    reason: Optional[str] = None
    input_summary: str
    autonomy_level: str


class ApprovalManager:
    """Manages approval workflow for high-risk operations."""

    def __init__(self, config: dict):
        """Initialize approval manager with configuration.

        Args:
            config: Configuration dictionary with keys:
                - level: Autonomy level (supervised, semi_auto, full_auto)
                - auto_approve: Set of tool names to auto-approve
                - always_ask: Set of tool names that always require approval
                - max_session_allowlist_size: Max items in session allowlist
        """
        self.auto_approve: Set[str] = set(config.get("auto_approve", [
            "get_property",
            "list_properties",
            "get_property_recap",
            "get_conversation_history",
            "list_contracts",
            "get_portfolio_summary",
            "get_pipeline_summary",
            "get_follow_up_queue",
            "get_insights",
            "get_activity_timeline",
            "get_property_heartbeat",
            "list_workflows",
            "list_bulk_operations",
            "list_watchlists",
            "get_comps_dashboard",
            "get_score_breakdown",
            "get_top_properties",
            "get_daily_digest",
            "get_pipeline_status",
            "list_notifications",
            "get_analytics",
            "search_research",
            "find_similar_properties",
            "get_research_dossier",
            "get_research_status",
            "get_deal_status",
            "list_deal_types",
            "preview_deal_type",
            "calculate_deal",
            "calculate_mao",
            "what_if_deal",
            "compare_strategies",
            "list_offers",
            "get_offer_details",
            "draft_offer_letter"
        ]))

        self.always_ask: Set[str] = set(config.get("always_ask", [
            "send_contract",
            "withdraw_offer",
            "skip_trace_property",
            "delete_property",
            "delete_contact",
            "delete_contract",
            "cancel_all_campaigns",
            "clear_conversation_history",
            "bulk_operation",
            "execute_workflow"
        ]))

        self.session_allowlist: Dict[str, Set[str]] = {}  # session_id -> set of approved tools
        self.audit_log: List[ApprovalLogEntry] = []
        self.autonomy_level = config.get("level", "supervised")
        self.max_session_allowlist_size = config.get("max_session_allowlist_size", 50)

        # Risk-based configuration
        self.risk_categories = {
            "critical": [
                "delete_property",
                "delete_contact",
                "delete_contract",
                "cancel_all_campaigns",
                "clear_conversation_history"
            ],
            "high": [
                "send_contract",
                "withdraw_offer",
                "skip_trace_property",
                "bulk_operation"
            ],
            "medium": [
                "update_property",
                "create_property",
                "add_contact",
                "attach_required_contracts",
                "execute_workflow",
                "create_voice_campaign",
                "create_offer",
                "accept_offer",
                "reject_offer",
                "counter_offer"
            ],
            "low": [
                "get_property",
                "list_properties",
                "get_property_recap",
                "enrich_property",
                "generate_property_recap",
                "make_property_phone_call",
                "create_scheduled_task"
            ]
        }

    def _get_risk_level(self, tool_name: str) -> str:
        """Determine risk level for a tool.

        Args:
            tool_name: Name of the tool being called

        Returns:
            Risk level: critical, high, medium, or low
        """
        for level, tools in self.risk_categories.items():
            if tool_name in tools:
                return level
        return "medium"  # Default to medium for unknown tools

    def _summarize_input(self, input_data: Dict[str, Any], max_length: int = 100) -> str:
        """Create a safe summary of input data for audit logging.

        Args:
            input_data: Raw input data
            max_length: Maximum length of summary

        Returns:
            Safe summary string with sensitive data redacted
        """
        # Scrub sensitive fields
        scrubbed = self._scrub_sensitive_data(input_data)

        # Convert to string and truncate
        summary = json.dumps(scrubbed, separators=(",", ":"))
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
        return summary

    def _scrub_sensitive_data(self, data: Any) -> Any:
        """Redact sensitive information from data structures.

        Args:
            data: Any data structure (dict, list, or primitive)

        Returns:
            Data with sensitive fields redacted
        """
        if isinstance(data, dict):
            scrubbed = {}
            for key, value in data.items():
                # Check for sensitive keys
                if any(sensitive in key.lower() for sensitive in [
                    "password", "token", "api_key", "secret", "key",
                    "ssn", "social_security", "credit_card", "account_number"
                ]):
                    scrubbed[key] = "***REDACTED***"
                elif isinstance(value, (dict, list)):
                    scrubbed[key] = self._scrub_sensitive_data(value)
                else:
                    scrubbed[key] = value
            return scrubbed
        elif isinstance(data, list):
            return [self._scrub_sensitive_data(item) for item in data]
        else:
            return data

    async def requires_approval(
        self,
        tool_name: str,
        session_id: Optional[str] = None
    ) -> bool:
        """Check if a tool requires approval.

        Args:
            tool_name: Name of the tool to check
            session_id: Optional session ID for allowlist checking

        Returns:
            True if approval is required, False otherwise
        """
        # Full auto mode: no approvals
        if self.autonomy_level == "full_auto":
            return False

        # Check auto-approve list (read-only operations)
        if tool_name in self.auto_approve:
            return False

        # Check session allowlist
        if session_id and session_id in self.session_allowlist:
            if tool_name in self.session_allowlist[session_id]:
                return False

        # Check always-ask list
        if tool_name in self.always_ask:
            return True

        # Semi-auto mode: only ask for always_ask tools
        if self.autonomy_level == "semi_auto":
            return tool_name in self.always_ask

        # Supervised mode: ask for everything not auto-approved
        return True

    async def request_approval(
        self,
        session_id: str,
        tool_name: str,
        input_data: Dict[str, Any],
        db: Optional[Session] = None
    ) -> ApprovalResult:
        """Request approval for a tool execution.

        Args:
            session_id: Agent's session ID
            tool_name: Name of the tool requiring approval
            input_data: Input parameters for the tool
            db: Optional database session for persistent logging

        Returns:
            ApprovalResult with decision and reasoning
        """
        risk_level = self._get_risk_level(tool_name)
        timestamp = datetime.now()

        # Check if auto-approved
        if not await self.requires_approval(tool_name, session_id):
            result = ApprovalResult(
                granted=True,
                reason="Auto-approved (read-only or previously approved)",
                autonomy_level=self.autonomy_level,
                timestamp=timestamp
            )
            await self._log_approval(
                session_id=session_id,
                tool_name=tool_name,
                granted=True,
                risk_level=risk_level,
                timestamp=timestamp,
                reason=result.reason,
                input_summary=self._summarize_input(input_data),
                db=db
            )
            return result

        # Supervised mode: deny by default (requires explicit approval)
        if self.autonomy_level == "supervised":
            result = ApprovalResult(
                granted=False,
                reason=f"Manual approval required for {risk_level}-risk operation: {tool_name}. "
                      f"Use the approval API to grant permission.",
                autonomy_level=self.autonomy_level,
                timestamp=timestamp
            )
            await self._log_approval(
                session_id=session_id,
                tool_name=tool_name,
                granted=False,
                risk_level=risk_level,
                timestamp=timestamp,
                reason=result.reason,
                input_summary=self._summarize_input(input_data),
                db=db
            )
            return result

        # Semi-auto mode: grant unless it's critical
        if self.autonomy_level == "semi_auto":
            if risk_level == "critical":
                result = ApprovalResult(
                    granted=False,
                    reason=f"Critical-risk operations require explicit approval even in semi-auto mode",
                    autonomy_level=self.autonomy_level,
                    timestamp=timestamp
                )
                await self._log_approval(
                    session_id=session_id,
                    tool_name=tool_name,
                    granted=False,
                    risk_level=risk_level,
                    timestamp=timestamp,
                    reason=result.reason,
                    input_summary=self._summarize_input(input_data),
                    db=db
                )
                return result
            else:
                result = ApprovalResult(
                    granted=True,
                    reason=f"Auto-approved in semi-auto mode (risk level: {risk_level})",
                    autonomy_level=self.autonomy_level,
                    timestamp=timestamp
                )
                await self._log_approval(
                    session_id=session_id,
                    tool_name=tool_name,
                    granted=True,
                    risk_level=risk_level,
                    timestamp=timestamp,
                    reason=result.reason,
                    input_summary=self._summarize_input(input_data),
                    db=db
                )
                return result

        # Full auto mode: grant everything
        result = ApprovalResult(
            granted=True,
            reason="Auto-approved in full-autonomy mode",
            autonomy_level=self.autonomy_level,
            timestamp=timestamp
        )
        await self._log_approval(
            session_id=session_id,
            tool_name=tool_name,
            granted=True,
            risk_level=risk_level,
            timestamp=timestamp,
            reason=result.reason,
            input_summary=self._summarize_input(input_data),
            db=db
        )
        return result

    async def grant_approval(
        self,
        session_id: str,
        tool_name: str,
        add_to_allowlist: bool = True,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Grant approval for a tool.

        Args:
            session_id: Agent's session ID
            tool_name: Name of the tool to approve
            add_to_allowlist: Whether to add to session allowlist for future auto-approval
            db: Optional database session

        Returns:
            Result dictionary
        """
        if add_to_allowlist:
            if session_id not in self.session_allowlist:
                self.session_allowlist[session_id] = set()

            # Enforce max allowlist size
            if len(self.session_allowlist[session_id]) >= self.max_session_allowlist_size:
                # Remove oldest entry
                self.session_allowlist[session_id].pop()

            self.session_allowlist[session_id].add(tool_name)

        return {
            "status": "approved",
            "tool_name": tool_name,
            "session_id": session_id,
            "added_to_allowlist": add_to_allowlist,
            "allowlist_size": len(self.session_allowlist.get(session_id, set()))
        }

    async def deny_approval(
        self,
        session_id: str,
        tool_name: str,
        reason: str,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Deny approval for a tool.

        Args:
            session_id: Agent's session ID
            tool_name: Name of the tool to deny
            reason: Reason for denial
            db: Optional database session

        Returns:
            Result dictionary
        """
        return {
            "status": "denied",
            "tool_name": tool_name,
            "session_id": session_id,
            "reason": reason
        }

    async def _log_approval(
        self,
        session_id: str,
        tool_name: str,
        granted: bool,
        risk_level: str,
        timestamp: datetime,
        reason: Optional[str],
        input_summary: str,
        db: Optional[Session] = None
    ):
        """Log approval decision to audit trail.

        Args:
            session_id: Agent's session ID
            tool_name: Name of the tool
            granted: Whether approval was granted
            risk_level: Risk level of the operation
            timestamp: When the decision was made
            reason: Reason for the decision
            input_summary: Safe summary of input data
            db: Optional database session for persistent logging
        """
        entry = ApprovalLogEntry(
            session_id=session_id,
            tool_name=tool_name,
            granted=granted,
            risk_level=risk_level,
            timestamp=timestamp,
            reason=reason,
            input_summary=input_summary,
            autonomy_level=self.autonomy_level
        )

        self.audit_log.append(entry)

        # TODO: Implement persistent logging to database if db session provided
        # if db:
        #     log_entry = ApprovalLog(
        #         session_id=session_id,
        #         tool_name=tool_name,
        #         granted=granted,
        #         risk_level=risk_level,
        #         timestamp=timestamp,
        #         reason=reason,
        #         input_summary=input_summary,
        #         autonomy_level=self.autonomy_level
        #     )
        #     db.add(log_entry)
        #     db.commit()

    def get_audit_log(
        self,
        session_id: Optional[str] = None,
        limit: int = 100
    ) -> List[ApprovalLogEntry]:
        """Retrieve approval audit log.

        Args:
            session_id: Optional session ID to filter by
            limit: Maximum number of entries to return

        Returns:
            List of audit log entries
        """
        log = self.audit_log

        if session_id:
            log = [entry for entry in log if entry.session_id == session_id]

        # Return most recent first
        return sorted(log, key=lambda x: x.timestamp, reverse=True)[:limit]

    def clear_session_allowlist(self, session_id: str) -> None:
        """Clear the allowlist for a session.

        Args:
            session_id: Session ID to clear
        """
        if session_id in self.session_allowlist:
            del self.session_allowlist[session_id]

    def get_session_allowlist(self, session_id: str) -> Set[str]:
        """Get the current allowlist for a session.

        Args:
            session_id: Session ID to query

        Returns:
            Set of approved tool names
        """
        return self.session_allowlist.get(session_id, set()).copy()

    def set_autonomy_level(self, level: str) -> None:
        """Change the autonomy level.

        Args:
            level: New autonomy level (supervised, semi_auto, full_auto)
        """
        if level not in ["supervised", "semi_auto", "full_auto"]:
            raise ValueError(f"Invalid autonomy level: {level}")

        self.autonomy_level = level

    def get_autonomy_level(self) -> str:
        """Get current autonomy level.

        Returns:
            Current autonomy level
        """
        return self.autonomy_level


# Global singleton instance
approval_manager = ApprovalManager(config={
    "level": "supervised",  # Default to supervised mode for safety
    "auto_approve": [
        "get_property",
        "list_properties",
        "get_property_recap",
        "get_conversation_history",
        "list_contracts",
        "get_portfolio_summary",
        "get_pipeline_summary",
        "get_follow_up_queue",
        "get_insights",
        "get_activity_timeline",
        "get_property_heartbeat",
        "list_workflows",
        "list_bulk_operations",
        "list_watchlists",
        "get_comps_dashboard",
        "get_score_breakdown",
        "get_top_properties",
        "get_daily_digest",
        "get_pipeline_status",
        "list_notifications",
        "get_analytics",
        "search_research",
        "find_similar_properties",
        "get_research_dossier",
        "get_research_status",
        "get_deal_status",
        "list_deal_types",
        "preview_deal_type",
        "calculate_deal",
        "calculate_mao",
        "what_if_deal",
        "compare_strategies",
        "list_offers",
        "get_offer_details",
        "draft_offer_letter",
        "get_research_status",
        "get_property_history",
        "get_notification_summary",
        "poll_for_updates",
        "get_contract_status",
        "get_signing_status",
        "get_property_recap",
        "list_property_notes",
        "get_property_history",
        "get_conversation_history",
        "what_did_we_discuss",
        "list_scheduled_tasks",
        "get_contract_status_voice",
        "list_contracts_voice",
        "check_property_contract_readiness_voice",
        "get_property_insights"
    ],
    "always_ask": [
        "send_contract",
        "withdraw_offer",
        "skip_trace_property",
        "delete_property",
        "delete_contact",
        "delete_contract",
        "cancel_all_campaigns",
        "clear_conversation_history",
        "bulk_operation",
        "execute_workflow"
    ],
    "max_session_allowlist_size": 50
})
