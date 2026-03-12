from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.deal_type_config import DealTypeConfig
from app.models.property import Property
from app.schemas.deal_type_config import (
    DealTypeConfigCreate,
    DealTypeConfigUpdate,
    DealTypeConfigResponse,
)
from app.services.deal_type_service import apply_deal_type, get_deal_type_summary

router = APIRouter(prefix="/deal-types", tags=["deal-types"])


@router.get("/", response_model=list[DealTypeConfigResponse])
def list_deal_types(
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    """List all deal type configs."""
    query = db.query(DealTypeConfig)
    if active_only:
        query = query.filter(DealTypeConfig.is_active == True)
    return query.order_by(DealTypeConfig.name).all()


@router.post("/", response_model=DealTypeConfigResponse, status_code=201)
def create_deal_type(
    config: DealTypeConfigCreate,
    db: Session = Depends(get_db),
):
    """Create a custom deal type config."""
    existing = db.query(DealTypeConfig).filter(
        DealTypeConfig.name == config.name,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Deal type '{config.name}' already exists")

    db_config = DealTypeConfig(
        **config.model_dump(),
        is_builtin=False,
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


@router.get("/{name}", response_model=DealTypeConfigResponse)
def get_deal_type(name: str, db: Session = Depends(get_db)):
    """Get a deal type config by name."""
    config = db.query(DealTypeConfig).filter(DealTypeConfig.name == name).first()
    if not config:
        raise HTTPException(status_code=404, detail=f"Deal type '{name}' not found")
    return config


@router.put("/{name}", response_model=DealTypeConfigResponse)
def update_deal_type(
    name: str,
    update: DealTypeConfigUpdate,
    db: Session = Depends(get_db),
):
    """Update a deal type config."""
    config = db.query(DealTypeConfig).filter(DealTypeConfig.name == name).first()
    if not config:
        raise HTTPException(status_code=404, detail=f"Deal type '{name}' not found")

    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    db.commit()
    db.refresh(config)
    return config


@router.delete("/{name}", status_code=204)
def delete_deal_type(name: str, db: Session = Depends(get_db)):
    """Delete a custom deal type config. Cannot delete built-in configs."""
    config = db.query(DealTypeConfig).filter(DealTypeConfig.name == name).first()
    if not config:
        raise HTTPException(status_code=404, detail=f"Deal type '{name}' not found")
    if config.is_builtin:
        raise HTTPException(status_code=403, detail="Cannot delete built-in deal types")

    db.delete(config)
    db.commit()
    return None


@router.post("/{name}/preview")
def preview_deal_type(
    name: str,
    property_id: int,
    db: Session = Depends(get_db),
):
    """Preview what would be triggered if this deal type was applied to a property (dry run)."""
    config = db.query(DealTypeConfig).filter(
        DealTypeConfig.name == name,
        DealTypeConfig.is_active == True,
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail=f"Deal type '{name}' not found")

    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    from app.models.contract import Contract
    from app.models.todo import Todo
    from app.models.contact import Contact

    # Check which contracts would be created (not already existing)
    existing_contract_names = {
        c.name for c in db.query(Contract).filter(Contract.property_id == property_id).all()
    }
    new_contracts = [
        name for name in (config.contract_templates or [])
        if name not in existing_contract_names
    ]

    # Check which todos would be created
    existing_todo_titles = {
        t.title for t in db.query(Todo).filter(Todo.property_id == property_id).all()
    }
    new_todos = [
        item for item in (config.checklist or [])
        if item.get("title") not in existing_todo_titles
    ]

    # Check missing contacts
    existing_roles = {
        c.role.value for c in db.query(Contact).filter(Contact.property_id == property_id).all()
    }
    missing_roles = [
        role for role in (config.required_contact_roles or [])
        if role not in existing_roles
    ]

    return {
        "deal_type": config.display_name,
        "property_id": property_id,
        "property_address": property.address,
        "preview": True,
        "would_create_contracts": new_contracts,
        "would_skip_contracts": [
            n for n in (config.contract_templates or []) if n in existing_contract_names
        ],
        "would_create_todos": new_todos,
        "would_skip_todos": [
            item for item in (config.checklist or [])
            if item.get("title") in existing_todo_titles
        ],
        "missing_contact_roles": missing_roles,
        "present_contact_roles": [
            role for role in (config.required_contact_roles or [])
            if role in existing_roles
        ],
    }
