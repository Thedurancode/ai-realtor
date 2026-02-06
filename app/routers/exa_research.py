from fastapi import APIRouter, HTTPException
import httpx

from app.schemas.exa_research import (
    ExaPropertyDossierRequest,
    ExaResearchCreateRequest,
    ExaResearchResponse,
)
from app.services.exa_research_service import exa_research_service


router = APIRouter(prefix="/exa", tags=["exa-research"])


@router.post("/research/property-dossier", response_model=ExaResearchResponse)
async def create_property_dossier_research_task(request: ExaPropertyDossierRequest):
    """
    One-click property dossier task.

    Builds the investor-grade prompt server-side from address/strategy,
    then submits it to Exa Research.
    """
    try:
        instructions = exa_research_service.build_property_dossier_instructions(
            address=request.address,
            county=request.county,
            strategy=request.strategy,
        )
        raw = await exa_research_service.create_research_task(
            instructions=instructions,
            model=request.model,
        )
        return ExaResearchResponse(
            task_id=exa_research_service.extract_task_id(raw),
            status=exa_research_service.extract_status(raw),
            raw=raw,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code if exc.response is not None else 502
        detail = exc.response.text if exc.response is not None else str(exc)
        raise HTTPException(status_code=status, detail=detail)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Exa request failed: {exc}")


@router.post("/research", response_model=ExaResearchResponse)
async def create_exa_research_task(request: ExaResearchCreateRequest):
    """
    Create an Exa Research task.

    Mirrors:
    POST https://api.exa.ai/research/v1
    """
    try:
        raw = await exa_research_service.create_research_task(
            instructions=request.instructions,
            model=request.model,
        )
        return ExaResearchResponse(
            task_id=exa_research_service.extract_task_id(raw),
            status=exa_research_service.extract_status(raw),
            raw=raw,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code if exc.response is not None else 502
        detail = exc.response.text if exc.response is not None else str(exc)
        raise HTTPException(status_code=status, detail=detail)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Exa request failed: {exc}")


@router.get("/research/{task_id}", response_model=ExaResearchResponse)
async def get_exa_research_task(task_id: str):
    """
    Fetch an Exa Research task result.

    Mirrors:
    GET https://api.exa.ai/research/v1/{task_id}
    """
    try:
        raw = await exa_research_service.get_research_task(task_id=task_id)
        return ExaResearchResponse(
            task_id=exa_research_service.extract_task_id(raw) or task_id,
            status=exa_research_service.extract_status(raw),
            raw=raw,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code if exc.response is not None else 502
        detail = exc.response.text if exc.response is not None else str(exc)
        raise HTTPException(status_code=status, detail=detail)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Exa request failed: {exc}")
