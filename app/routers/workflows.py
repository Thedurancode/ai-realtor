"""Workflow template endpoints for multi-step voice-first operations."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.workflow_template_service import workflow_template_service

router = APIRouter(prefix="/workflows", tags=["workflows"])


class WorkflowExecuteRequest(BaseModel):
    template_name: str
    property_id: int | None = None
    property_query: str | None = None
    session_id: str = "default"
    execution_mode: str | None = None
    confirm_high_risk: bool = False


@router.get("/templates")
def list_workflow_templates():
    """List all available workflow templates."""
    return workflow_template_service.list_templates()


@router.post("/execute")
async def execute_workflow(request: WorkflowExecuteRequest, db: Session = Depends(get_db)):
    """Execute a named workflow template.

    Workflows delegate to the Voice Goal Planner which handles checkpoints,
    memory graph persistence, and safety gates.
    """
    return await workflow_template_service.execute(
        db=db,
        template_name=request.template_name,
        property_id=request.property_id,
        property_query=request.property_query,
        session_id=request.session_id,
        execution_mode=request.execution_mode,
        confirm_high_risk=request.confirm_high_risk,
    )
