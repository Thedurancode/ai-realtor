"""Remotion render job API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import List

from app.database import SessionLocal
from app.models.render_job import RenderJob
from app.schemas.render_job import RenderJobCreate, RenderJobResponse, RenderJobProgress, RenderJobList
from app.services.remotion_service import RemotionService

router = APIRouter(prefix="/v1/renders", tags=["renders"])


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


@router.post("", response_model=RenderJobResponse, status_code=status.HTTP_201_CREATED)
async def create_render_job(
    render_data: RenderJobCreate,
    db: Session = Depends(get_db),
    agent_id: int = Depends(get_agent_id)
):
    """
    Create a new render job.

    - **template_id**: Which template to use ('captioned-reel' or 'slideshow')
    - **composition_id**: Composition name within the template
    - **input_props**: Props to pass to the Remotion composition
    - **webhook_url**: Optional URL to receive completion notification
    """
    try:
        job = await RemotionService.create_render_job(
            db=db,
            agent_id=agent_id,
            template_id=render_data.template_id,
            composition_id=render_data.composition_id,
            input_props=render_data.input_props,
            webhook_url=render_data.webhook_url
        )
        return job.to_dict()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create render job: {str(e)}"
        )


@router.get("", response_model=RenderJobList)
async def list_render_jobs(
    db: Session = Depends(get_db),
    agent_id: int = Depends(get_agent_id)
):
    """List all render jobs for the authenticated agent."""
    jobs = RemotionService.list_render_jobs(db, agent_id)
    return RenderJobList(
        jobs=[job.to_dict() for job in jobs],
        total=len(jobs)
    )


@router.get("/{render_id}", response_model=RenderJobResponse)
async def get_render_job(
    render_id: str,
    db: Session = Depends(get_db),
    agent_id: int = Depends(get_agent_id)
):
    """Get details of a specific render job."""
    job = RemotionService.get_render_job(db, render_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Render job not found"
        )

    # Ensure agent owns this job
    if job.agent_id != agent_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this render job"
        )

    return job.to_dict()


@router.get("/{render_id}/progress", response_model=RenderJobProgress)
async def get_render_progress(
    render_id: str,
    db: Session = Depends(get_db),
    agent_id: int = Depends(get_agent_id)
):
    """Get real-time progress of a render job."""
    job = RemotionService.get_render_job(db, render_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Render job not found"
        )

    # Ensure agent owns this job
    if job.agent_id != agent_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this render job"
        )

    return RenderJobProgress(
        id=job.id,
        status=job.status,
        progress=job.progress,
        current_frame=job.current_frame,
        total_frames=job.total_frames,
        eta_seconds=job.eta_seconds
    )


@router.post("/{render_id}/cancel", response_model=RenderJobResponse)
async def cancel_render_job(
    render_id: str,
    db: Session = Depends(get_db),
    agent_id: int = Depends(get_agent_id)
):
    """Cancel a render job."""
    job = await RemotionService.cancel_render_job(db, render_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Render job not found"
        )

    # Ensure agent owns this job
    if job.agent_id != agent_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to cancel this render job"
        )

    return job.to_dict()
