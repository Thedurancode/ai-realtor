"""Timeline project API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import List
from uuid import uuid4

from app.database import SessionLocal
from app.models.timeline_project import TimelineProject
from app.models.render_job import RenderJob
from app.schemas.timeline import (
    TimelineProjectCreate,
    TimelineProjectUpdate,
    TimelineProjectResponse,
    TimelineProjectList,
    RenderFromTimelineRequest,
    RenderJobResponse,
)
from app.services.remotion_service import RemotionService

router = APIRouter(prefix="/v1/timeline", tags=["timeline"])


def get_db():
    """Dependency to get DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_agent_id(request: Request) -> int:
    """Dependency to get authenticated agent ID from request state."""
    agent_id = getattr(request.state, 'agent_id', None)
    if not agent_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication"
        )
    return agent_id


@router.post("", response_model=TimelineProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_timeline_project(
    project_data: TimelineProjectCreate,
    db: Session = Depends(get_db),
    agent_id: int = Depends(get_agent_id)
):
    """Create a new timeline video project."""
    project = TimelineProject(
        agent_id=agent_id,
        name=project_data.name,
        description=project_data.description,
        timeline_data=project_data.timeline_data.dict(),
        fps=project_data.fps,
        width=project_data.width,
        height=project_data.height,
        status="draft"
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project.to_dict()


@router.get("", response_model=TimelineProjectList)
async def list_timeline_projects(
    db: Session = Depends(get_db),
    agent_id: int = Depends(get_agent_id)
):
    """List all timeline projects for the authenticated agent."""
    projects = db.query(TimelineProject).filter(
        TimelineProject.agent_id == agent_id
    ).order_by(TimelineProject.created_at.desc()).all()
    return TimelineProjectList(
        projects=[p.to_dict() for p in projects],
        total=len(projects)
    )


@router.get("/{project_id}", response_model=TimelineProjectResponse)
async def get_timeline_project(
    project_id: str,
    db: Session = Depends(get_db),
    agent_id: int = Depends(get_agent_id)
):
    """Get details of a specific timeline project."""
    project = db.query(TimelineProject).filter(
        TimelineProject.id == project_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timeline project not found"
        )

    if project.agent_id != agent_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this project"
        )

    return project.to_dict()


@router.put("/{project_id}", response_model=TimelineProjectResponse)
async def update_timeline_project(
    project_id: str,
    project_data: TimelineProjectUpdate,
    db: Session = Depends(get_db),
    agent_id: int = Depends(get_agent_id)
):
    """Update a timeline project."""
    project = db.query(TimelineProject).filter(
        TimelineProject.id == project_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timeline project not found"
        )

    if project.agent_id != agent_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this project"
        )

    # Update fields
    if project_data.name is not None:
        project.name = project_data.name
    if project_data.description is not None:
        project.description = project_data.description
    if project_data.timeline_data is not None:
        project.timeline_data = project_data.timeline_data.dict()
    if project_data.fps is not None:
        project.fps = project_data.fps
    if project_data.width is not None:
        project.width = project_data.width
    if project_data.height is not None:
        project.height = project_data.height
    if project_data.status is not None:
        project.status = project_data.status

    db.commit()
    db.refresh(project)
    return project.to_dict()


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_timeline_project(
    project_id: str,
    db: Session = Depends(get_db),
    agent_id: int = Depends(get_agent_id)
):
    """Delete a timeline project."""
    project = db.query(TimelineProject).filter(
        TimelineProject.id == project_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timeline project not found"
        )

    if project.agent_id != agent_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this project"
        )

    db.delete(project)
    db.commit()


@router.post("/{project_id}/render", response_model=RenderJobResponse)
async def render_timeline_project(
    project_id: str,
    render_data: RenderFromTimelineRequest,
    db: Session = Depends(get_db),
    agent_id: int = Depends(get_agent_id)
):
    """Render a timeline project as a video."""
    # Get project
    project = db.query(TimelineProject).filter(
        TimelineProject.id == project_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timeline project not found"
        )

    if project.agent_id != agent_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to render this project"
        )

    # Create render job
    job = await RemotionService.create_render_job(
        db=db,
        agent_id=agent_id,
        template_id="timeline",
        composition_id="TimelineEditor",
        input_props=project.timeline_data,
        webhook_url=render_data.webhook_url
    )

    # Update project with render job reference
    project.render_job_id = job.id
    project.status = "rendering"
    db.commit()

    return job.to_dict()
