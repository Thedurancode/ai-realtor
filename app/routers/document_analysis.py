"""Document Analysis router - AI-powered document intelligence."""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import tempfile
import os

from app.database import get_db
from app.services.document_analysis_service import document_analysis_service

router = APIRouter(prefix="/documents", tags=["documents"])
logger = logging.getLogger(__name__)


# ── Schemas ──────────────────────────────────────────────────────────

class DocumentAnalyze(BaseModel):
    file_path: str
    document_type: str = Field(..., description="inspection_report, contract, appraisal, etc.")
    property_id: Optional[int] = None


class DocumentCompare(BaseModel):
    file_path_1: str
    file_path_2: str
    document_type: str


class DocumentChat(BaseModel):
    file_path: str
    question: str
    chat_history: Optional[List[dict]] = None


class ExtractIssues(BaseModel):
    file_path: str
    property_id: Optional[int] = None


class ExtractTerms(BaseModel):
    file_path: str
    property_id: Optional[int] = None


# ── Endpoints ────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a document for analysis."""
    try:
        # Save to temp file
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, file.filename)

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        return {
            "message": "Document uploaded successfully",
            "file_path": file_path,
            "filename": file.filename,
            "size": len(content)
        }

    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_document(body: DocumentAnalyze, db: Session = Depends(get_db)):
    """Analyze a document with AI.

    Extracts key information based on document type:
    - inspection_report: Issues, costs, safety hazards
    - contract: Terms, parties, dates, contingencies
    - appraisal: Value, comps, adjustments
    """
    try:
        result = await document_analysis_service.analyze_document(
            file_path=body.file_path,
            document_type=body.document_type,
            property_id=body.property_id
        )

        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    except Exception as e:
        logger.error(f"Error analyzing document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-issues")
async def extract_issues(body: ExtractIssues, db: Session = Depends(get_db)):
    """Extract issues from inspection report.

    Categorizes issues by severity (critical, major, minor)
    and provides repair cost estimates.
    """
    try:
        result = await document_analysis_service.analyze_document(
            file_path=body.file_path,
            document_type="inspection_report",
            property_id=body.property_id
        )

        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])

        # Return just the issues
        return {
            "issues": result.get("issues", []),
            "total_estimated_cost": result.get("total_estimated_cost", 0),
            "critical_issues_count": result.get("critical_issues_count", 0),
            "safety_hazards": result.get("safety_hazards", [])
        }

    except Exception as e:
        logger.error(f"Error extracting issues: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-terms")
async def extract_terms(body: ExtractTerms, db: Session = Depends(get_db)):
    """Extract key terms from contract.

    Extracts parties, price, contingencies, dates, and clauses.
    """
    try:
        result = await document_analysis_service.analyze_document(
            file_path=body.file_path,
            document_type="contract",
            property_id=body.property_id
        )

        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    except Exception as e:
        logger.error(f"Error extracting terms: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
async def compare_documents(body: DocumentCompare):
    """Compare two documents and highlight differences.

    Useful for:
    - Comparing two appraisals
    - Comparing contract versions
    - Comparing inspection reports
    """
    try:
        result = await document_analysis_service.compare_documents(
            file_path_1=body.file_path_1,
            file_path_2=body.file_path_2,
            document_type=body.document_type
        )

        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    except Exception as e:
        logger.error(f"Error comparing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
async def chat_with_document(body: DocumentChat):
    """Q&A with a document.

    Ask questions about a document and get AI-powered answers.
    Maintains chat history for follow-up questions.
    """
    try:
        result = await document_analysis_service.chat_with_document(
            file_path=body.file_path,
            question=body.question,
            chat_history=body.chat_history
        )

        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    except Exception as e:
        logger.error(f"Error in document chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/{file_path:path}")
async def get_document_summary(file_path: str):
    """Get a summary of any document.

    Provides:
    - Summary of key points
    - Important dates or deadlines
    - Action items or requirements
    - Any concerns or risks
    """
    try:
        result = await document_analysis_service.analyze_document(
            file_path=file_path,
            document_type="general",
            property_id=None
        )

        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "summary": result.get("summary", result.get("analysis", ""))
        }

    except Exception as e:
        logger.error(f"Error getting document summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types")
def list_document_types():
    """List all supported document types."""
    types = {
        "inspection_report": {
            "name": "Inspection Report",
            "description": "Property inspection report with issues and costs",
            "extracts": ["issues", "repair_costs", "safety_hazards", "recommendations"]
        },
        "contract": {
            "name": "Contract",
            "description": "Real estate contract or agreement",
            "extracts": ["parties", "price", "terms", "contingencies", "dates", "clauses"]
        },
        "appraisal": {
            "name": "Appraisal",
            "description": "Property appraisal report",
            "extracts": ["appraised_value", "comps", "adjustments", "property_details"]
        },
        "disclosure": {
            "name": "Disclosure Statement",
            "description": "Property disclosure document",
            "extracts": ["disclosures", "defects", "issues"]
        },
        "deed": {
            "name": "Deed",
            "description": "Property deed or title document",
            "extracts": ["owners", "restrictions", "easements", "encumbrances"]
        }
    }
    return types
