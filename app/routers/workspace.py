"""Workspace management API router."""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional

from app.database import get_db
from app.models.workspace import Workspace, WorkspaceAPIKey, CommandPermission, API_SCOPES
from app.services.workspace_service import workspace_service

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


# Request/Response schemas
class CreateWorkspaceRequest(BaseModel):
    name: str
    owner_email: EmailStr
    owner_name: str
    subscription_tier: str = "free"


class CreateAPIKeyRequest(BaseModel):
    name: str
    scopes: List[str]
    agent_id: Optional[int] = None
    expires_days: Optional[int] = None


class SetPermissionRequest(BaseModel):
    command_pattern: str
    permission: str  # allow, deny, require_approval
    agent_id: Optional[int] = None
    reason: Optional[str] = None


@router.post("/")
async def create_workspace(
    request: CreateWorkspaceRequest,
    db: Session = Depends(get_db)
):
    """Create a new workspace (multi-tenant SaaS)."""
    try:
        workspace = workspace_service.create_workspace(
            db=db,
            name=request.name,
            owner_email=request.owner_email,
            owner_name=request.owner_name,
            subscription_tier=request.subscription_tier
        )

        return {
            "workspace_id": workspace.id,
            "name": workspace.name,
            "owner_email": workspace.owner_email,
            "subscription_tier": workspace.subscription_tier,
            "api_key": workspace.initial_api_key,  # Only shown once!
            "created_at": workspace.created_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{workspace_id}")
async def get_workspace(
    workspace_id: int,
    db: Session = Depends(get_db)
):
    """Get workspace details."""
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.deleted_at.is_(None)
    ).first()

    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Get usage stats
    stats = workspace_service.get_workspace_stats(db, workspace_id)

    return {
        "id": workspace.id,
        "name": workspace.name,
        "owner_email": workspace.owner_email,
        "owner_name": workspace.owner_name,
        "subscription_tier": workspace.subscription_tier,
        "is_active": workspace.is_active,
        "settings": workspace.settings,
        "created_at": workspace.created_at.isoformat(),
        "stats": stats
    }


@router.get("/{workspace_id}/stats")
async def get_workspace_stats(
    workspace_id: int,
    db: Session = Depends(get_db)
):
    """Get workspace usage statistics."""
    stats = workspace_service.get_workspace_stats(db, workspace_id)

    if not stats:
        raise HTTPException(status_code=404, detail="Workspace not found")

    return stats


@router.post("/{workspace_id}/api-keys")
async def create_api_key(
    workspace_id: int,
    request: CreateAPIKeyRequest,
    db: Session = Depends(get_db)
):
    """Create a new API key for the workspace."""
    try:
        api_key, key_obj = workspace_service.create_api_key(
            db=db,
            workspace_id=workspace_id,
            name=request.name,
            scopes=request.scopes,
            agent_id=request.agent_id,
            expires_days=request.expires_days
        )

        return {
            "api_key": api_key,  # Only shown once!
            "id": key_obj.id,
            "name": key_obj.name,
            "key_prefix": key_obj.key_prefix,
            "scopes": key_obj.scopes,
            "expires_at": key_obj.expires_at.isoformat() if key_obj.expires_at else None
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{workspace_id}/api-keys")
async def list_api_keys(
    workspace_id: int,
    db: Session = Depends(get_db)
):
    """List all API keys for a workspace."""
    keys = workspace_service.list_api_keys(db, workspace_id)

    return {
        "workspace_id": workspace_id,
        "api_keys": keys
    }


@router.post("/api-keys/{key_id}/revoke")
async def revoke_api_key(
    key_id: int,
    db: Session = Depends(get_db)
):
    """Revoke an API key."""
    success = workspace_service.revoke_api_key(db, key_id)

    if not success:
        raise HTTPException(status_code=404, detail="API key not found")

    return {"message": "API key revoked successfully"}


@router.post("/{workspace_id}/permissions")
async def set_permission(
    workspace_id: int,
    request: SetPermissionRequest,
    db: Session = Depends(get_db)
):
    """Set a command permission rule."""
    try:
        perm = workspace_service.set_command_permission(
            db=db,
            workspace_id=workspace_id,
            command_pattern=request.command_pattern,
            permission=request.permission,
            agent_id=request.agent_id,
            reason=request.reason
        )

        return {
            "id": perm.id,
            "command_pattern": perm.command_pattern,
            "permission": perm.permission,
            "agent_id": perm.agent_id,
            "reason": perm.reason
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/scopes")
async def list_available_scopes():
    """List all available API scopes."""
    return API_SCOPES
