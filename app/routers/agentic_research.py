from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.agentic_property import ResearchProperty
from app.schemas.agentic_research import (
    AgenticJobCreateResponse,
    AgenticJobStatusResponse,
    DossierEnvelope,
    PropertyEnvelope,
    ResearchInput,
)
from app.services.agentic.pipeline import agentic_research_service


router = APIRouter(prefix="/agentic", tags=["agentic-research"])


@router.post("/jobs", response_model=AgenticJobCreateResponse, status_code=201)
async def create_agentic_job(
    payload: ResearchInput,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    job = await agentic_research_service.create_job(db=db, payload=payload)
    background_tasks.add_task(agentic_research_service.run_job, job.id)

    return AgenticJobCreateResponse(
        job_id=job.id,
        property_id=job.research_property_id,
        trace_id=job.trace_id,
        status=job.status.value,
    )


@router.get("/jobs/{job_id}", response_model=AgenticJobStatusResponse)
def get_agentic_job(job_id: int, db: Session = Depends(get_db)):
    job = agentic_research_service.get_job(db=db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return AgenticJobStatusResponse(
        id=job.id,
        property_id=job.research_property_id,
        trace_id=job.trace_id,
        status=job.status.value,
        progress=job.progress,
        current_step=job.current_step,
        error_message=job.error_message,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


@router.get("/properties/{property_id}", response_model=PropertyEnvelope)
def get_agentic_property(property_id: int, db: Session = Depends(get_db)):
    research_property = (
        db.query(ResearchProperty)
        .filter(ResearchProperty.id == property_id)
        .first()
    )
    if not research_property:
        raise HTTPException(status_code=404, detail="Property not found")

    latest_job = agentic_research_service.get_latest_completed_job_for_property(db=db, property_id=property_id)
    if latest_job is None:
        return PropertyEnvelope(property_id=property_id, latest_job_id=None, output=None)

    output = agentic_research_service.get_full_output(
        db=db,
        property_id=property_id,
        job_id=latest_job.id,
    )
    return PropertyEnvelope(property_id=property_id, latest_job_id=latest_job.id, output=output)


@router.get("/properties/{property_id}/dossier", response_model=DossierEnvelope)
def get_agentic_dossier(property_id: int, db: Session = Depends(get_db)):
    latest_job = agentic_research_service.get_latest_completed_job_for_property(db=db, property_id=property_id)
    if latest_job is None:
        raise HTTPException(status_code=404, detail="No completed job found for property")

    output = agentic_research_service.get_full_output(db=db, property_id=property_id, job_id=latest_job.id)
    if not output or not output.get("dossier", {}).get("markdown"):
        raise HTTPException(status_code=404, detail="Dossier not found")

    return DossierEnvelope(
        property_id=property_id,
        latest_job_id=latest_job.id,
        markdown=output["dossier"]["markdown"],
    )


@router.post("/research", response_model=PropertyEnvelope)
async def run_agentic_research_sync(payload: ResearchInput, db: Session = Depends(get_db)):
    # Uses service-level session handling to avoid returning from a closed transaction.
    job = await agentic_research_service.run_sync(payload=payload)

    output = agentic_research_service.get_full_output(
        db=db,
        property_id=job.research_property_id,
        job_id=job.id,
    )

    return PropertyEnvelope(
        property_id=job.research_property_id,
        latest_job_id=job.id,
        output=output,
    )
