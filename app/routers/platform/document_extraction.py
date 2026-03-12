"""
Document Extraction API Routes
Upload documents and extract data using OCR + AI
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import io

from app.database import SessionLocal
from app.services.document_extraction import extract_from_upload
from app.models.property import Property
from app.models.contact import Contact
from app.models.contract import Contract
from app.models.agent import Agent
from app.auth import get_current_agent

router = APIRouter(prefix="/documents", tags=["document-extraction"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# Document Upload & Extraction
# ============================================================================

@router.post("/extract")
async def extract_document(
    file: UploadFile = File(...),
    extraction_type: str = Form("property"),  # property, contract, contact
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """
    Upload a document (PDF, PNG, JPG) and extract structured data using OCR + AI

    Returns extracted data that can be used to create properties, contacts, or contracts
    """
    # Validate file type
    allowed_types = ["application/pdf", "image/png", "image/jpeg", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )

    # Read file content
    file_content = await file.read()

    # Check file size (max 10MB)
    if len(file_content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 10MB")

    # Determine file type for OCR
    file_type_map = {
        "application/pdf": "pdf",
        "image/png": "png",
        "image/jpeg": "jpg",
        "image/jpg": "jpg"
    }
    file_type = file_type_map.get(file.content_type, "pdf")

    # Extract data
    result = await extract_from_upload(
        file_content=file_content,
        file_type=file_type,
        extraction_type=extraction_type
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Extraction failed")
        )

    # Return extracted data
    return {
        "extraction_type": extraction_type,
        "raw_text": result.get("raw_text", "")[:500] + "..." if len(result.get("raw_text", "")) > 500 else result.get("raw_text", ""),
        "extracted_data": result.get("structured_data", {}),
        "file_name": file.filename,
        "file_size": len(file_content)
    }


# ============================================================================
# Smart Property Creation from Document
# ============================================================================

@router.post("/extract/property")
async def extract_and_create_property(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """
    Upload a property listing document (PDF/Image) and auto-create a property

    Extracts: address, city, state, price, beds, baths, sqft, etc.
    """
    file_content = await file.read()

    if len(file_content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large")

    file_type = "pdf" if file.content_type == "application/pdf" else "png"
    if file.content_type in ["image/jpeg", "image/jpg"]:
        file_type = "jpg"

    # Extract property data
    result = await extract_from_upload(
        file_content=file_content,
        file_type=file_type,
        extraction_type="property"
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Extraction failed")
        )

    data = result.get("structured_data", {})

    # Validate required fields
    if not data.get("address"):
        raise HTTPException(
            status_code=400,
            detail="Could not extract address from document"
        )

    # Create property
    try:
        property = Property(
            title=data.get("address", "Untitled Property"),
            address=data["address"],
            city=data.get("city", ""),
            state=data.get("state", ""),
            zip_code=data.get("zip_code", ""),
            price=data.get("price") or 0,
            bedrooms=data.get("bedrooms"),
            bathrooms=data.get("bathrooms"),
            square_feet=data.get("square_feet"),
            year_built=data.get("year_built"),
            lot_size=data.get("lot_size"),
            property_type=data.get("property_type"),
            description=data.get("description"),
            agent_id=current_agent.id
        )

        db.add(property)
        db.commit()
        db.refresh(property)

        return {
            "success": True,
            "property_id": property.id,
            "extracted_data": data,
            "message": "Property created successfully from document"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create property: {str(e)}"
        )


# ============================================================================
# Smart Contact Creation from Document
# ============================================================================

@router.post("/extract/contact")
async def extract_and_create_contact(
    file: UploadFile = File(...),
    property_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """
    Upload a business card or contact document and auto-create a contact

    Extracts: name, email, phone, company, title, role
    """
    file_content = await file.read()

    if len(file_content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large")

    file_type = "pdf" if file.content_type == "application/pdf" else "png"
    if file.content_type in ["image/jpeg", "image/jpg"]:
        file_type = "jpg"

    # Extract contact data
    result = await extract_from_upload(
        file_content=file_content,
        file_type=file_type,
        extraction_type="contact"
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Extraction failed")
        )

    data = result.get("structured_data", {})

    # Validate required fields
    if not data.get("full_name"):
        raise HTTPException(
            status_code=400,
            detail="Could not extract name from document"
        )

    # Create contact
    try:
        from app.models.contact import Contact

        contact = Contact(
            name=data["full_name"],
            email=data.get("email"),
            phone=data.get("phone", [None])[0] if data.get("phone") else None,
            company=data.get("company"),
            title=data.get("title"),
            role=data.get("role", "other"),
            property_id=property_id,
            agent_id=current_agent.id
        )

        db.add(contact)
        db.commit()
        db.refresh(contact)

        return {
            "success": True,
            "contact_id": contact.id,
            "extracted_data": data,
            "message": "Contact created successfully from document"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create contact: {str(e)}"
        )


# ============================================================================
# Contract Analysis from Document
# ============================================================================

@router.post("/extract/contract")
async def analyze_contract_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """
    Upload a contract document and extract key terms

    Extracts: parties, dates, amounts, clauses, terms
    """
    file_content = await file.read()

    if len(file_content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large")

    file_type = "pdf" if file.content_type == "application/pdf" else "png"
    if file.content_type in ["image/jpeg", "image/jpg"]:
        file_type = "jpg"

    # Extract contract data
    result = await extract_from_upload(
        file_content=file_content,
        file_type=file_type,
        extraction_type="contract"
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Extraction failed")
        )

    return {
        "success": True,
        "contract_analysis": result.get("structured_data", {}),
        "raw_text": result.get("raw_text", "")[:1000] + "..." if len(result.get("raw_text", "")) > 1000 else result.get("raw_text", ""),
        "message": "Contract analyzed successfully"
    }


# ============================================================================
# Text-only Extraction (for copy-paste)
# ============================================================================

class TextExtractRequest(BaseModel):
    text: str
    extraction_type: str = "property"  # property, contract, contact


@router.post("/extract/text")
async def extract_from_text(
    request: TextExtractRequest,
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """
    Extract structured data from pasted text (useful for emails, chat logs, etc.)
    """
    if len(request.text) < 50:
        raise HTTPException(
            status_code=400,
            detail="Text too short. Provide at least 50 characters."
        )

    if len(request.text) > 50000:
        raise HTTPException(
            status_code=400,
            detail="Text too long. Max 50,000 characters."
        )

    from app.services.document_extraction import document_extractor

    result = await document_extractor._llm_extract(
        text=request.text,
        extraction_type=request.extraction_type
    )

    return {
        "extraction_type": request.extraction_type,
        "input_text_length": len(request.text),
        "extracted_data": result
    }


# ============================================================================
# Batch Extraction
# ============================================================================

@router.post("/extract/batch")
async def extract_batch_documents(
    files: List[UploadFile] = File(...),
    extraction_type: str = Form("property"),
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """
    Extract data from multiple documents at once

    Returns: Array of extraction results
    """
    if len(files) > 10:
        raise HTTPException(
            status_code=400,
            detail="Too many files. Max 10 per batch."
        )

    results = []

    for file in files:
        try:
            file_content = await file.read()

            if len(file_content) > 10 * 1024 * 1024:
                results.append({
                    "file_name": file.filename,
                    "success": False,
                    "error": "File too large"
                })
                continue

            file_type = "pdf" if file.content_type == "application/pdf" else "png"
            if file.content_type in ["image/jpeg", "image/jpg"]:
                file_type = "jpg"

            result = await extract_from_upload(
                file_content=file_content,
                file_type=file_type,
                extraction_type=extraction_type
            )

            results.append({
                "file_name": file.filename,
                "success": result.get("success", False),
                "extracted_data": result.get("structured_data", {}),
                "error": result.get("error")
            })

        except Exception as e:
            results.append({
                "file_name": file.filename,
                "success": False,
                "error": str(e)
            })

    return {
        "batch_size": len(files),
        "successful": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
        "results": results
    }
