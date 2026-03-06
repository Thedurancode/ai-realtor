"""
Listing Presentation Router

POST /listing-presentation/generate  - returns all components as JSON
POST /listing-presentation/pdf       - returns branded PDF download
POST /listing-presentation/email     - generate and email to seller
"""

import os
import logging
from typing import Optional, Dict, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.listing_presentation_service import (
    generate_presentation,
    generate_presentation_pdf,
    email_presentation,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/listing-presentation", tags=["Listing Presentation"])


# ── Request / Response schemas ──────────────────────────────────────────

class PresentationRequest(BaseModel):
    address: str = Field(..., description="Full property address")
    property_details: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional property details: beds, baths, sqft, year_built, lot_size, features",
    )
    recipient_email: Optional[str] = Field(None, description="Email to send PDF to")
    recipient_name: Optional[str] = Field(None, description="Recipient name for email")


# ── Endpoints ───────────────────────────────────────────────────────────

@router.post("/generate")
async def generate(request: PresentationRequest, db: Session = Depends(get_db)):
    """Generate a complete listing presentation and return all components as JSON."""
    try:
        result = await generate_presentation(
            db,
            request.address,
            request.property_details,
        )
        return result
    except Exception as e:
        logger.exception("Failed to generate listing presentation")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pdf")
async def generate_pdf(request: PresentationRequest, db: Session = Depends(get_db)):
    """Generate a branded listing presentation PDF and return it as a download."""
    try:
        presentation, pdf_path = await generate_presentation_pdf(
            db,
            request.address,
            request.property_details,
        )
        safe_name = request.address.replace(" ", "_").replace(",", "").replace("/", "-")[:40]
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"Listing_Presentation_{safe_name}.pdf",
            background=BackgroundTasks(),  # file cleanup handled by OS temp
        )
    except Exception as e:
        logger.exception("Failed to generate listing presentation PDF")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/email")
async def email_to_seller(request: PresentationRequest, db: Session = Depends(get_db)):
    """Generate a listing presentation PDF and email it to the seller."""
    if not request.recipient_email:
        raise HTTPException(status_code=400, detail="recipient_email is required")
    if not request.recipient_name:
        raise HTTPException(status_code=400, detail="recipient_name is required")

    try:
        result = await email_presentation(
            db,
            request.address,
            request.recipient_email,
            request.recipient_name,
            request.property_details,
        )
        return result
    except Exception as e:
        logger.exception("Failed to email listing presentation")
        raise HTTPException(status_code=500, detail=str(e))
