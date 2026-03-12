"""Bulk Operations router."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.bulk_operations_service import bulk_operations_service

router = APIRouter(prefix="/bulk", tags=["bulk"])


class BulkExecuteRequest(BaseModel):
    operation: str
    property_ids: list[int] | None = None
    filters: dict | None = None
    params: dict | None = None


@router.post("/execute")
async def execute_bulk_operation(body: BulkExecuteRequest, db: Session = Depends(get_db)):
    """Execute an operation across multiple properties."""
    try:
        return await bulk_operations_service.execute(
            db=db,
            operation=body.operation,
            property_ids=body.property_ids,
            filters=body.filters,
            params=body.params,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/operations")
def list_bulk_operations():
    """List available bulk operations with descriptions."""
    return {"operations": bulk_operations_service.list_operations()}
