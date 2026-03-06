"""CMA (Comparative Market Analysis) Report router."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.cma_report_service import (
    generate_cma_report,
    get_cma_preview,
    email_cma_report,
)

router = APIRouter(prefix="/cma", tags=["cma"])


class CMAGenerateRequest(BaseModel):
    property_id: int
    agent_brand_id: Optional[int] = None


class CMAEmailRequest(BaseModel):
    property_id: int
    recipient_email: EmailStr
    recipient_name: Optional[str] = "Client"
    agent_brand_id: Optional[int] = None


@router.post("/generate")
def generate_cma(request: CMAGenerateRequest, db: Session = Depends(get_db)):
    """Generate a CMA report PDF for a property. Returns the PDF as a file download."""
    try:
        pdf_bytes, filename = generate_cma_report(
            db,
            property_id=request.property_id,
            agent_brand_id=request.agent_brand_id,
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate CMA report: {e}")


@router.post("/email")
def email_cma(request: CMAEmailRequest, db: Session = Depends(get_db)):
    """Generate a CMA report and email it to a recipient."""
    try:
        result = email_cma_report(
            db,
            property_id=request.property_id,
            recipient_email=request.recipient_email,
            recipient_name=request.recipient_name or "Client",
            agent_brand_id=request.agent_brand_id,
        )
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Report generated but email failed: {result.get('email', {}).get('error', 'Unknown error')}",
            )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate/email CMA: {e}")


@router.get("/preview/{property_id}")
def preview_cma(property_id: int, db: Session = Depends(get_db)):
    """Get CMA data as JSON for frontend preview (no PDF generation)."""
    try:
        return get_cma_preview(db, property_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate CMA preview: {e}")
