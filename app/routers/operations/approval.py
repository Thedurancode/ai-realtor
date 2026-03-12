"""Approval API router.

Provides endpoints for managing approval workflow for high-risk operations.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.database import get_db
from app.services.approval import approval_manager


router = APIRouter(prefix="/approval", tags=["Approval"])


# Pydantic models
class ApprovalRequestRequest(BaseModel):
    """Request approval for a tool execution."""
    session_id: str = Field(..., description="Agent's session ID")
    tool_name: str = Field(..., description="Name of the tool requiring approval")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Input parameters for the tool")


class ApprovalGrantRequest(BaseModel):
    """Grant approval for a tool."""
    session_id: str = Field(..., description="Agent's session ID")
    tool_name: str = Field(..., description="Name of the tool to approve")
    add_to_allowlist: bool = Field(True, description="Add to session allowlist for future auto-approval")


class ApprovalDenyRequest(BaseModel):
    """Deny approval for a tool."""
    session_id: str = Field(..., description="Agent's session ID")
    tool_name: str = Field(..., description="Name of the tool to deny")
    reason: str = Field(..., description="Reason for denial")


class AutonomyLevelRequest(BaseModel):
    """Change autonomy level."""
    level: str = Field(..., description="New autonomy level (supervised, semi_auto, full_auto)")


@router.post("/request")
async def request_approval(
    request: ApprovalRequestRequest,
    db: Session = Depends(get_db)
):
    """Request approval for a tool execution.

    Returns whether the operation is approved and the reasoning.
    """
    result = await approval_manager.request_approval(
        session_id=request.session_id,
        tool_name=request.tool_name,
        input_data=request.input_data,
        db=db
    )

    return {
        "granted": result.granted,
        "reason": result.reason,
        "autonomy_level": result.autonomy_level,
        "timestamp": result.timestamp.isoformat()
    }


@router.post("/grant")
async def grant_approval(
    request: ApprovalGrantRequest,
    db: Session = Depends(get_db)
):
    """Grant approval for a tool.

    Optionally adds the tool to the session's allowlist for future auto-approval.
    """
    result = await approval_manager.grant_approval(
        session_id=request.session_id,
        tool_name=request.tool_name,
        add_to_allowlist=request.add_to_allowlist,
        db=db
    )

    return result


@router.post("/deny")
async def deny_approval(
    request: ApprovalDenyRequest,
    db: Session = Depends(get_db)
):
    """Deny approval for a tool."""
    result = await approval_manager.deny_approval(
        session_id=request.session_id,
        tool_name=request.tool_name,
        reason=request.reason,
        db=db
    )

    return result


@router.get("/audit-log")
async def get_audit_log(
    session_id: Optional[str] = None,
    limit: int = 100
):
    """Retrieve approval audit log.

    Optionally filter by session ID.
    """
    log = approval_manager.get_audit_log(session_id=session_id, limit=limit)

    return {
        "total_entries": len(log),
        "entries": [
            {
                "session_id": entry.session_id,
                "tool_name": entry.tool_name,
                "granted": entry.granted,
                "risk_level": entry.risk_level,
                "timestamp": entry.timestamp.isoformat(),
                "reason": entry.reason,
                "input_summary": entry.input_summary,
                "autonomy_level": entry.autonomy_level
            }
            for entry in log
        ]
    }


@router.get("/allowlist/{session_id}")
async def get_session_allowlist(session_id: str):
    """Get the current allowlist for a session."""
    allowlist = approval_manager.get_session_allowlist(session_id)

    return {
        "session_id": session_id,
        "approved_tools": list(allowlist),
        "total": len(allowlist)
    }


@router.delete("/allowlist/{session_id}")
async def clear_session_allowlist(session_id: str):
    """Clear the allowlist for a session."""
    approval_manager.clear_session_allowlist(session_id)

    return {
        "status": "cleared",
        "session_id": session_id
    }


@router.get("/autonomy-level")
async def get_autonomy_level():
    """Get current autonomy level."""
    level = approval_manager.get_autonomy_level()

    return {
        "level": level,
        "description": {
            "supervised": "All operations require approval except read-only",
            "semi_auto": "Non-critical operations auto-approved, critical require approval",
            "full_auto": "All operations auto-approved"
        }.get(level, "Unknown")
    }


@router.put("/autonomy-level")
async def set_autonomy_level(request: AutonomyLevelRequest):
    """Change the autonomy level."""
    try:
        approval_manager.set_autonomy_level(request.level)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "status": "updated",
        "level": request.level
    }


@router.get("/risk-categories")
async def get_risk_categories():
    """Get risk categories for all tools."""
    return approval_manager.risk_categories


@router.get("/config")
async def get_approval_config():
    """Get current approval configuration."""
    return {
        "autonomy_level": approval_manager.autonomy_level,
        "auto_approve_count": len(approval_manager.auto_approve),
        "always_ask_count": len(approval_manager.always_ask),
        "max_session_allowlist_size": approval_manager.max_session_allowlist_size,
        "active_sessions": len(approval_manager.session_allowlist)
    }
