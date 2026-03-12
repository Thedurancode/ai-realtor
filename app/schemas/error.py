"""Standardized API error responses."""
from typing import Any, Optional
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Individual error detail."""
    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    """Unified error response format for all API endpoints."""
    error: str  # machine-readable error code e.g. "validation_error", "not_found"
    message: str  # human-readable message
    request_id: Optional[str] = None
    details: Optional[list[ErrorDetail]] = None


class HTTPExceptionResponse(BaseModel):
    """For OpenAPI docs — maps to standard HTTPException."""
    detail: str
