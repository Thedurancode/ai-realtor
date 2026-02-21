"""
Contract Templates API

Manage contract templates that auto-attach to properties.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.contract_template import ContractTemplate, ContractRequirement
from app.schemas.contract_template import (
    ContractTemplateCreate,
    ContractTemplateUpdate,
    ContractTemplateResponse
)

router = APIRouter(prefix="/contract-templates", tags=["contract-templates"])


@router.post("/", response_model=ContractTemplateResponse, status_code=201)
def create_template(
    template: ContractTemplateCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new contract template.

    Example: Create template for NY Property Disclosure Statement
    that auto-attaches to all NY properties.
    """
    new_template = ContractTemplate(**template.model_dump())
    db.add(new_template)
    db.commit()
    db.refresh(new_template)
    return new_template


@router.get("/", response_model=List[ContractTemplateResponse])
def list_templates(
    state: Optional[str] = None,
    category: Optional[str] = None,
    requirement: Optional[ContractRequirement] = None,
    is_active: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List all contract templates with optional filters.

    Filters:
    - state: Filter by state (e.g., "NY")
    - category: Filter by category (listing, purchase, disclosure, etc.)
    - requirement: Filter by requirement (required, recommended, optional)
    - is_active: Filter by active status
    """
    limit = min(limit, 200)
    query = db.query(ContractTemplate)

    if state:
        query = query.filter(
            (ContractTemplate.state == state) |
            (ContractTemplate.state == None)
        )

    if category:
        query = query.filter(ContractTemplate.category == category)

    if requirement:
        query = query.filter(ContractTemplate.requirement == requirement)

    if is_active is not None:
        query = query.filter(ContractTemplate.is_active == is_active)

    templates = query.order_by(
        ContractTemplate.priority.desc(),
        ContractTemplate.name
    ).offset(offset).limit(limit).all()

    return templates


@router.get("/{template_id}", response_model=ContractTemplateResponse)
def get_template(template_id: int, db: Session = Depends(get_db)):
    """Get a contract template by ID"""
    template = db.query(ContractTemplate).filter(
        ContractTemplate.id == template_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return template


@router.patch("/{template_id}", response_model=ContractTemplateResponse)
def update_template(
    template_id: int,
    template_update: ContractTemplateUpdate,
    db: Session = Depends(get_db)
):
    """Update a contract template"""
    template = db.query(ContractTemplate).filter(
        ContractTemplate.id == template_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    update_data = template_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(template, field, value)

    db.commit()
    db.refresh(template)
    return template


@router.delete("/{template_id}", status_code=204)
def delete_template(template_id: int, db: Session = Depends(get_db)):
    """Delete a contract template"""
    template = db.query(ContractTemplate).filter(
        ContractTemplate.id == template_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    db.delete(template)
    db.commit()
    return None


@router.post("/{template_id}/activate", response_model=ContractTemplateResponse)
def activate_template(template_id: int, db: Session = Depends(get_db)):
    """Activate a contract template"""
    template = db.query(ContractTemplate).filter(
        ContractTemplate.id == template_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    template.is_active = True
    db.commit()
    db.refresh(template)
    return template


@router.post("/{template_id}/deactivate", response_model=ContractTemplateResponse)
def deactivate_template(template_id: int, db: Session = Depends(get_db)):
    """Deactivate a contract template"""
    template = db.query(ContractTemplate).filter(
        ContractTemplate.id == template_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    template.is_active = False
    db.commit()
    db.refresh(template)
    return template
