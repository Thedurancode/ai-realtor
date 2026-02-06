"""
Deal Type Service

Orchestrates deal type workflows: auto-attach contracts,
create checklist todos, check required contacts.
"""
from datetime import date, timedelta
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.models.property import Property, DealType
from app.models.deal_type_config import DealTypeConfig
from app.models.contract import Contract, ContractStatus, RequirementSource
from app.models.contract_template import ContractTemplate
from app.models.contact import Contact
from app.models.todo import Todo, TodoPriority, TodoStatus

logger = logging.getLogger(__name__)

PRIORITY_MAP = {
    "low": TodoPriority.LOW,
    "medium": TodoPriority.MEDIUM,
    "high": TodoPriority.HIGH,
    "urgent": TodoPriority.URGENT,
}


def apply_deal_type(
    db: Session,
    property: Property,
    deal_type_name: str,
    clear_previous: bool = False,
) -> dict:
    """
    Main orchestrator: apply a deal type to a property.

    1. Optionally clear previous deal type's contracts/todos
    2. Look up DealTypeConfig
    3. Auto-attach matching contract templates
    4. Create checklist todos
    5. Return summary of what was created

    Args:
        clear_previous: If True, removes draft contracts and pending todos
                        that were auto-attached by the previous deal type
                        before applying the new one. Completed/signed
                        contracts are never removed.
    """
    config = db.query(DealTypeConfig).filter(
        DealTypeConfig.name == deal_type_name,
        DealTypeConfig.is_active == True,
    ).first()

    if not config:
        return {
            "success": False,
            "error": f"Deal type config '{deal_type_name}' not found or inactive",
        }

    # Clear previous deal type artifacts if switching
    removed_contracts = []
    removed_todos = []
    if clear_previous and property.deal_type:
        old_config = db.query(DealTypeConfig).filter(
            DealTypeConfig.name == property.deal_type.value,
        ).first()
        if old_config:
            removed_contracts, removed_todos = _clear_deal_type_artifacts(
                db, property, old_config
            )

    # Set deal_type on property
    deal_type_enum = None
    try:
        deal_type_enum = DealType(deal_type_name)
    except ValueError:
        pass  # Custom deal type, not in enum — that's fine
    property.deal_type = deal_type_enum
    db.commit()

    # 1. Auto-attach contracts from config
    attached_contracts = _attach_contracts_from_config(db, property, config)

    # 2. Create checklist todos
    created_todos = _create_checklist_todos(db, property, config)

    # 3. Check missing contacts
    missing_contacts = get_missing_contacts(db, property, config)

    summary = {
        "success": True,
        "property_id": property.id,
        "property_address": property.address,
        "deal_type": config.display_name,
        "contracts_attached": len(attached_contracts),
        "contract_names": [c.name for c in attached_contracts],
        "todos_created": len(created_todos),
        "todo_titles": [t.title for t in created_todos],
        "missing_contacts": missing_contacts,
        "all_contacts_present": len(missing_contacts) == 0,
    }

    if clear_previous:
        summary["contracts_removed"] = len(removed_contracts)
        summary["contracts_removed_names"] = removed_contracts
        summary["todos_removed"] = len(removed_todos)
        summary["todos_removed_titles"] = removed_todos

    return summary


def _clear_deal_type_artifacts(
    db: Session, property: Property, old_config: DealTypeConfig
) -> tuple[list[str], list[str]]:
    """
    Remove draft contracts and pending todos that were created by the
    previous deal type. Never removes completed/signed contracts.

    Returns (removed_contract_names, removed_todo_titles).
    """
    removed_contracts = []
    removed_todos = []

    # Remove draft contracts that match old config's template names
    if old_config.contract_templates:
        old_contracts = db.query(Contract).filter(
            Contract.property_id == property.id,
            Contract.name.in_(old_config.contract_templates),
            Contract.status == ContractStatus.DRAFT,
        ).all()
        for c in old_contracts:
            removed_contracts.append(c.name)
            db.delete(c)

    # Remove pending todos that match old config's checklist titles
    if old_config.checklist:
        old_titles = [item.get("title") for item in old_config.checklist if item.get("title")]
        old_todos = db.query(Todo).filter(
            Todo.property_id == property.id,
            Todo.title.in_(old_titles),
            Todo.status.in_([TodoStatus.PENDING, TodoStatus.IN_PROGRESS]),
        ).all()
        for t in old_todos:
            removed_todos.append(t.title)
            db.delete(t)

    if removed_contracts or removed_todos:
        db.commit()

    return removed_contracts, removed_todos


def _attach_contracts_from_config(
    db: Session, property: Property, config: DealTypeConfig
) -> list[Contract]:
    """Auto-attach contracts listed in the deal type config."""
    if not config.contract_templates:
        return []

    created = []
    for template_name in config.contract_templates:
        # Check if contract already exists
        existing = db.query(Contract).filter(
            Contract.property_id == property.id,
            Contract.name == template_name,
        ).first()
        if existing:
            continue

        # Try to find a matching ContractTemplate for docuseal_template_id
        template = db.query(ContractTemplate).filter(
            ContractTemplate.name == template_name,
            ContractTemplate.is_active == True,
        ).first()

        contract = Contract(
            property_id=property.id,
            name=template_name,
            description=f"Auto-attached by deal type: {config.display_name}",
            docuseal_template_id=template.docuseal_template_id if template else None,
            status=ContractStatus.DRAFT,
            is_required=True,
            requirement_source=RequirementSource.AUTO_ATTACHED,
            requirement_reason=f"Required for {config.display_name} deal type",
        )
        db.add(contract)
        created.append(contract)

    if created:
        db.commit()
        for c in created:
            db.refresh(c)

    return created


def _create_checklist_todos(
    db: Session, property: Property, config: DealTypeConfig
) -> list[Todo]:
    """Create checklist todos from deal type config."""
    if not config.checklist:
        return []

    created = []
    for item in config.checklist:
        title = item.get("title", "")
        # Skip if todo with same title already exists
        existing = db.query(Todo).filter(
            Todo.property_id == property.id,
            Todo.title == title,
        ).first()
        if existing:
            continue

        priority_str = item.get("priority", "medium")
        priority = PRIORITY_MAP.get(priority_str, TodoPriority.MEDIUM)

        due_days = item.get("due_days")
        due_date = None
        if due_days:
            due_date = date.today() + timedelta(days=due_days)

        todo = Todo(
            property_id=property.id,
            title=title,
            description=item.get("description"),
            priority=priority,
            status=TodoStatus.PENDING,
            due_date=due_date,
        )
        db.add(todo)
        created.append(todo)

    if created:
        db.commit()
        for t in created:
            db.refresh(t)

    return created


def get_missing_contacts(
    db: Session,
    property: Property,
    config_or_name=None,
) -> list[str]:
    """
    Check which required contact roles are missing for this deal type.
    Returns list of missing role names.
    """
    config = config_or_name
    if isinstance(config_or_name, str):
        config = db.query(DealTypeConfig).filter(
            DealTypeConfig.name == config_or_name,
        ).first()
    elif config is None and property.deal_type:
        config = db.query(DealTypeConfig).filter(
            DealTypeConfig.name == property.deal_type.value,
        ).first()

    if not config or not config.required_contact_roles:
        return []

    # Get existing contact roles for this property
    existing_contacts = db.query(Contact).filter(
        Contact.property_id == property.id,
    ).all()
    existing_roles = {c.role.value for c in existing_contacts}

    missing = [
        role for role in config.required_contact_roles
        if role not in existing_roles
    ]
    return missing


def get_deal_type_summary(db: Session, property: Property) -> dict:
    """
    Voice-friendly summary of deal progress.
    Returns contracts status, checklist progress, missing contacts.
    """
    if not property.deal_type:
        return {
            "property_id": property.id,
            "property_address": property.address,
            "deal_type": None,
            "message": "No deal type set for this property.",
        }

    config = db.query(DealTypeConfig).filter(
        DealTypeConfig.name == property.deal_type.value,
    ).first()

    if not config:
        return {
            "property_id": property.id,
            "property_address": property.address,
            "deal_type": property.deal_type.value,
            "message": f"Deal type is {property.deal_type.value} but no config found.",
        }

    # Contracts status
    contracts = db.query(Contract).filter(
        Contract.property_id == property.id,
    ).all()
    completed_contracts = [c for c in contracts if c.status == ContractStatus.COMPLETED]
    pending_contracts = [c for c in contracts if c.status != ContractStatus.COMPLETED]

    # Todos status
    todos = db.query(Todo).filter(
        Todo.property_id == property.id,
    ).all()
    completed_todos = [t for t in todos if t.status == TodoStatus.COMPLETED]
    pending_todos = [t for t in todos if t.status != TodoStatus.COMPLETED]

    # Missing contacts
    missing_contacts = get_missing_contacts(db, property, config)

    return {
        "property_id": property.id,
        "property_address": property.address,
        "deal_type": config.display_name,
        "deal_type_name": config.name,
        "contracts": {
            "total": len(contracts),
            "completed": len(completed_contracts),
            "pending": len(pending_contracts),
            "completed_names": [c.name for c in completed_contracts],
            "pending_names": [c.name for c in pending_contracts],
        },
        "checklist": {
            "total": len(todos),
            "completed": len(completed_todos),
            "pending": len(pending_todos),
            "pending_items": [
                {"title": t.title, "priority": t.priority.value if t.priority else "medium"}
                for t in pending_todos
            ],
        },
        "contacts": {
            "missing_roles": missing_contacts,
            "all_present": len(missing_contacts) == 0,
        },
        "ready_to_close": (
            len(pending_contracts) == 0
            and len(missing_contacts) == 0
            and len(contracts) > 0
        ),
    }
