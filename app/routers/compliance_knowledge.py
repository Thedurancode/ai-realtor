"""
Compliance Knowledge API - CRUD operations for compliance rules
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
import csv
import io

from app.database import get_db
from app.models.compliance_rule import ComplianceRule, ComplianceRuleTemplate
from app.schemas.compliance import (
    ComplianceRuleCreate,
    ComplianceRuleUpdate,
    ComplianceRuleResponse,
    ComplianceRuleAIGenerateRequest,
    ComplianceRuleTemplateResponse,
)
from app.services.compliance_knowledge_service import compliance_knowledge_service

router = APIRouter(prefix="/compliance/knowledge", tags=["compliance-knowledge"])


# ========== CREATE OPERATIONS ==========

@router.post("/rules", response_model=ComplianceRuleResponse, status_code=201)
async def create_compliance_rule(
    rule: ComplianceRuleCreate,
    agent_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Create a new compliance rule.

    Example:
    {
        "state": "NY",
        "rule_code": "NY-LEAD-001",
        "category": "disclosure",
        "title": "Lead Paint Disclosure",
        "description": "Properties built before 1978 require lead paint disclosure",
        "rule_type": "threshold",
        "field_to_check": "year_built",
        "condition": "< 1978",
        "severity": "critical",
        "requires_document": true,
        "document_type": "lead_paint_disclosure"
    }
    """

    # Check for duplicate rule_code
    existing = db.query(ComplianceRule).filter(
        ComplianceRule.rule_code == rule.rule_code.upper()
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Rule code '{rule.rule_code}' already exists. Use PATCH to update or choose different code."
        )

    # Validate rule logic
    rule_dict = rule.model_dump()
    validation_errors = compliance_knowledge_service.validate_rule(rule_dict)
    if validation_errors:
        raise HTTPException(status_code=400, detail=validation_errors)

    # Create rule
    new_rule = ComplianceRule(
        **rule_dict,
        rule_code=rule.rule_code.upper(),
        state=rule.state.upper(),
        created_by=agent_id
    )

    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)

    return new_rule


@router.post("/rules/bulk", response_model=dict)
async def bulk_create_rules(
    rules: List[ComplianceRuleCreate],
    skip_duplicates: bool = True,
    agent_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Create multiple rules at once.
    Useful for importing knowledge bases.
    """

    created = []
    skipped = []
    errors = []

    for rule_data in rules:
        try:
            # Check for duplicates
            existing = db.query(ComplianceRule).filter(
                ComplianceRule.rule_code == rule_data.rule_code.upper()
            ).first()

            if existing:
                if skip_duplicates:
                    skipped.append(rule_data.rule_code)
                    continue
                else:
                    raise ValueError(f"Duplicate rule_code: {rule_data.rule_code}")

            # Validate
            rule_dict = rule_data.model_dump()
            validation_errors = compliance_knowledge_service.validate_rule(rule_dict)
            if validation_errors:
                errors.append({
                    "rule_code": rule_data.rule_code,
                    "errors": validation_errors
                })
                continue

            # Create
            new_rule = ComplianceRule(
                **rule_dict,
                rule_code=rule_data.rule_code.upper(),
                state=rule_data.state.upper(),
                created_by=agent_id
            )
            db.add(new_rule)
            created.append(rule_data.rule_code)

        except Exception as e:
            errors.append({
                "rule_code": rule_data.rule_code,
                "error": str(e)
            })

    db.commit()

    return {
        "created": len(created),
        "skipped": len(skipped),
        "errors": len(errors),
        "created_rules": created,
        "skipped_rules": skipped,
        "error_details": errors
    }


@router.post("/rules/import-csv", response_model=dict)
async def import_rules_from_csv(
    file: UploadFile = File(...),
    agent_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Import compliance rules from CSV file.

    CSV Format:
    state,rule_code,category,title,description,rule_type,field_to_check,condition,severity,requires_document,document_type
    """

    content = await file.read()
    csv_data = io.StringIO(content.decode('utf-8'))
    reader = csv.DictReader(csv_data)

    rules = []
    for row in reader:
        # Convert CSV row to rule object
        rule_dict = compliance_knowledge_service.csv_row_to_rule(row)
        try:
            rules.append(ComplianceRuleCreate(**rule_dict))
        except Exception as e:
            # Skip invalid rows
            continue

    # Use bulk create
    return await bulk_create_rules(rules, skip_duplicates=True, agent_id=agent_id, db=db)


@router.post("/rules/ai-generate", response_model=ComplianceRuleResponse)
async def generate_rule_with_ai(
    request: ComplianceRuleAIGenerateRequest,
    agent_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Use AI to generate a compliance rule from natural language description.

    Example:
    {
        "state": "CA",
        "natural_language_rule": "In California, all homes built before 1960 must have an earthquake retrofit inspection certificate before sale",
        "category": "safety"
    }
    """

    generated_rule = await compliance_knowledge_service.generate_rule_with_ai(
        state=request.state,
        natural_language=request.natural_language_rule,
        category=request.category,
        legal_citation=request.legal_citation
    )

    # Create the rule
    new_rule = ComplianceRule(
        **generated_rule,
        created_by=agent_id,
        is_draft=True  # Mark as draft for review
    )

    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)

    return new_rule


# ========== READ OPERATIONS ==========

@router.get("/rules", response_model=List[ComplianceRuleResponse])
def list_compliance_rules(
    state: Optional[str] = None,
    city: Optional[str] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    is_active: Optional[bool] = True,
    is_draft: Optional[bool] = None,
    rule_type: Optional[str] = None,
    search: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all compliance rules with advanced filtering.

    Query parameters:
    - state: Filter by state (e.g., "NY")
    - city: Filter by city
    - category: Filter by category (disclosure, safety, etc.)
    - severity: Filter by severity (critical, high, medium, low)
    - is_active: Show only active rules (default: true)
    - is_draft: Filter draft rules
    - rule_type: Filter by rule type
    - search: Search in title, description, rule_code
    - tags: Filter by tags (can specify multiple)
    """

    query = db.query(ComplianceRule)

    # Apply filters
    if state:
        query = query.filter(ComplianceRule.state == state.upper())

    if city:
        query = query.filter(ComplianceRule.city.ilike(f"%{city}%"))

    if category:
        query = query.filter(ComplianceRule.category == category)

    if severity:
        query = query.filter(ComplianceRule.severity == severity)

    if is_active is not None:
        query = query.filter(ComplianceRule.is_active == is_active)

    if is_draft is not None:
        query = query.filter(ComplianceRule.is_draft == is_draft)

    if rule_type:
        query = query.filter(ComplianceRule.rule_type == rule_type)

    # Search in text fields
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (ComplianceRule.title.ilike(search_term)) |
            (ComplianceRule.description.ilike(search_term)) |
            (ComplianceRule.rule_code.ilike(search_term))
        )

    # Filter by tags
    if tags:
        for tag in tags:
            query = query.filter(ComplianceRule.tags.contains([tag]))

    # Order by most recently updated
    query = query.order_by(ComplianceRule.updated_at.desc())

    return query.offset(skip).limit(limit).all()


@router.get("/rules/{rule_id}", response_model=ComplianceRuleResponse)
def get_compliance_rule(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific compliance rule by ID"""

    rule = db.query(ComplianceRule).filter(ComplianceRule.id == rule_id).first()

    if not rule:
        raise HTTPException(status_code=404, detail="Compliance rule not found")

    return rule


@router.get("/rules/code/{rule_code}", response_model=ComplianceRuleResponse)
def get_rule_by_code(
    rule_code: str,
    db: Session = Depends(get_db)
):
    """Get a compliance rule by its unique code (e.g., "NY-LEAD-001")"""

    rule = db.query(ComplianceRule).filter(
        ComplianceRule.rule_code == rule_code.upper()
    ).first()

    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule '{rule_code}' not found")

    return rule


@router.get("/rules/{rule_id}/history", response_model=List[ComplianceRuleResponse])
def get_rule_history(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """Get version history for a rule"""

    rule = db.query(ComplianceRule).filter(ComplianceRule.id == rule_id).first()

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    # Get all versions (current rule and all previous versions)
    versions = db.query(ComplianceRule).filter(
        (ComplianceRule.id == rule_id) |
        (ComplianceRule.rule_code == rule.rule_code)
    ).order_by(ComplianceRule.version.desc()).all()

    return versions


@router.get("/states", response_model=List[dict])
def get_available_states(db: Session = Depends(get_db)):
    """Get list of states with compliance rules"""

    states = db.query(
        ComplianceRule.state,
        func.count(ComplianceRule.id).label('rule_count')
    ).filter(
        ComplianceRule.is_active == True
    ).group_by(
        ComplianceRule.state
    ).all()

    return [
        {"state": state, "rule_count": count}
        for state, count in states
    ]


@router.get("/categories", response_model=List[dict])
def get_rule_categories(
    state: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get list of categories with rule counts"""

    query = db.query(
        ComplianceRule.category,
        func.count(ComplianceRule.id).label('rule_count')
    ).filter(ComplianceRule.is_active == True)

    if state:
        query = query.filter(ComplianceRule.state == state.upper())

    categories = query.group_by(ComplianceRule.category).all()

    return [
        {"category": cat, "rule_count": count}
        for cat, count in categories
    ]


@router.get("/export/csv")
def export_rules_to_csv(
    state: Optional[str] = None,
    category: Optional[str] = None,
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    """Export compliance rules to CSV"""

    query = db.query(ComplianceRule).filter(ComplianceRule.is_active == is_active)

    if state:
        query = query.filter(ComplianceRule.state == state.upper())

    if category:
        query = query.filter(ComplianceRule.category == category)

    rules = query.all()

    # Generate CSV
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        'rule_code', 'state', 'city', 'category', 'title', 'description',
        'rule_type', 'field_to_check', 'condition', 'severity',
        'requires_document', 'document_type', 'is_active', 'tags'
    ])

    writer.writeheader()
    for rule in rules:
        writer.writerow({
            'rule_code': rule.rule_code,
            'state': rule.state,
            'city': rule.city or '',
            'category': rule.category,
            'title': rule.title,
            'description': rule.description,
            'rule_type': rule.rule_type,
            'field_to_check': rule.field_to_check or '',
            'condition': rule.condition or '',
            'severity': rule.severity,
            'requires_document': rule.requires_document,
            'document_type': rule.document_type or '',
            'is_active': rule.is_active,
            'tags': ','.join(rule.tags) if rule.tags else ''
        })

    output.seek(0)

    filename = f"compliance_rules_{state or 'all'}_{category or 'all'}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ========== UPDATE OPERATIONS ==========

@router.patch("/rules/{rule_id}", response_model=ComplianceRuleResponse)
async def update_compliance_rule(
    rule_id: int,
    rule_update: ComplianceRuleUpdate,
    create_new_version: bool = False,
    agent_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Update a compliance rule.

    Parameters:
    - create_new_version: If true, creates a new version instead of updating in-place
    """

    existing_rule = db.query(ComplianceRule).filter(ComplianceRule.id == rule_id).first()

    if not existing_rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    update_data = rule_update.model_dump(exclude_unset=True)

    # Normalize state if provided
    if 'state' in update_data:
        update_data['state'] = update_data['state'].upper()

    # Validate updated rule
    merged_data = {**existing_rule.__dict__, **update_data}
    validation_errors = compliance_knowledge_service.validate_rule(merged_data)
    if validation_errors:
        raise HTTPException(status_code=400, detail=validation_errors)

    if create_new_version:
        # Create new version
        existing_rule.is_active = False  # Deactivate old version

        # Prepare data for new version
        new_version_data = {k: v for k, v in existing_rule.__dict__.items()
                           if not k.startswith('_') and k not in ['id', 'created_at']}
        new_version_data.update(update_data)
        new_version_data['version'] = existing_rule.version + 1
        new_version_data['parent_rule_id'] = existing_rule.id
        new_version_data['created_by'] = agent_id
        new_version_data['created_at'] = datetime.utcnow()
        new_version_data['updated_at'] = datetime.utcnow()

        new_version = ComplianceRule(**new_version_data)

        db.add(new_version)
        db.commit()
        db.refresh(new_version)

        return new_version
    else:
        # Update in place
        for field, value in update_data.items():
            setattr(existing_rule, field, value)

        existing_rule.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(existing_rule)

        return existing_rule


@router.post("/rules/{rule_id}/activate")
def activate_rule(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """Activate a rule (set is_active = True)"""

    rule = db.query(ComplianceRule).filter(ComplianceRule.id == rule_id).first()

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    rule.is_active = True
    rule.updated_at = datetime.utcnow()

    db.commit()

    return {"status": "activated", "rule_id": rule_id, "rule_code": rule.rule_code}


@router.post("/rules/{rule_id}/deactivate")
def deactivate_rule(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """Deactivate a rule (set is_active = False) - soft delete"""

    rule = db.query(ComplianceRule).filter(ComplianceRule.id == rule_id).first()

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    rule.is_active = False
    rule.updated_at = datetime.utcnow()

    db.commit()

    return {"status": "deactivated", "rule_id": rule_id, "rule_code": rule.rule_code}


@router.post("/rules/{rule_id}/publish")
def publish_draft_rule(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """Publish a draft rule (set is_draft = False)"""

    rule = db.query(ComplianceRule).filter(ComplianceRule.id == rule_id).first()

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    # Validate before publishing
    validation_errors = compliance_knowledge_service.validate_rule(rule.__dict__)
    if validation_errors:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot publish: {validation_errors}"
        )

    rule.is_draft = False
    rule.is_active = True
    rule.updated_at = datetime.utcnow()

    db.commit()

    return {"status": "published", "rule_id": rule_id, "rule_code": rule.rule_code}


# ========== DELETE OPERATIONS ==========

@router.delete("/rules/{rule_id}")
def delete_compliance_rule(
    rule_id: int,
    hard_delete: bool = False,
    db: Session = Depends(get_db)
):
    """
    Delete a compliance rule.

    Parameters:
    - hard_delete: If false (default), performs soft delete (sets is_active=False)
                   If true, permanently deletes from database
    """

    rule = db.query(ComplianceRule).filter(ComplianceRule.id == rule_id).first()

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    if hard_delete:
        # Permanent deletion
        db.delete(rule)
        db.commit()
        return {
            "status": "permanently_deleted",
            "rule_id": rule_id,
            "rule_code": rule.rule_code
        }
    else:
        # Soft delete
        rule.is_active = False
        rule.updated_at = datetime.utcnow()
        db.commit()
        return {
            "status": "deactivated",
            "rule_id": rule_id,
            "rule_code": rule.rule_code,
            "message": "Rule deactivated (soft delete). Use hard_delete=true to permanently delete."
        }


@router.delete("/rules/bulk")
def bulk_delete_rules(
    rule_ids: List[int],
    hard_delete: bool = False,
    db: Session = Depends(get_db)
):
    """Delete multiple rules at once"""

    deleted = []
    not_found = []

    for rule_id in rule_ids:
        rule = db.query(ComplianceRule).filter(ComplianceRule.id == rule_id).first()

        if not rule:
            not_found.append(rule_id)
            continue

        if hard_delete:
            db.delete(rule)
        else:
            rule.is_active = False
            rule.updated_at = datetime.utcnow()

        deleted.append(rule_id)

    db.commit()

    return {
        "deleted": len(deleted),
        "not_found": len(not_found),
        "deleted_rules": deleted,
        "not_found_rules": not_found,
        "delete_type": "permanent" if hard_delete else "soft"
    }


# ========== CLONE OPERATIONS ==========

@router.post("/rules/{rule_id}/clone", response_model=ComplianceRuleResponse)
def clone_rule(
    rule_id: int,
    new_state: Optional[str] = None,
    new_city: Optional[str] = None,
    new_rule_code: Optional[str] = None,
    agent_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Clone a rule to create a copy (useful for adapting rules to different states/cities)
    """

    original_rule = db.query(ComplianceRule).filter(ComplianceRule.id == rule_id).first()

    if not original_rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    # Create clone
    rule_dict = {
        key: value for key, value in original_rule.__dict__.items()
        if key not in ['id', '_sa_instance_state', 'created_at', 'updated_at', 'version', 'parent_rule_id']
    }

    # Override with new values
    if new_state:
        rule_dict['state'] = new_state.upper()
    if new_city:
        rule_dict['city'] = new_city
    if new_rule_code:
        rule_dict['rule_code'] = new_rule_code.upper()
    else:
        # Auto-generate new rule code
        import random
        rule_dict['rule_code'] = f"{rule_dict['state']}-{original_rule.category.upper()}-{random.randint(100,999)}"

    rule_dict['created_by'] = agent_id
    rule_dict['is_draft'] = True  # Mark as draft for review
    rule_dict['version'] = 1
    rule_dict['parent_rule_id'] = None

    cloned_rule = ComplianceRule(**rule_dict)

    db.add(cloned_rule)
    db.commit()
    db.refresh(cloned_rule)

    return cloned_rule


@router.post("/rules/clone-state-rules")
async def clone_state_rules(
    source_state: str,
    target_state: str,
    agent_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Clone all rules from one state to another.
    Useful for creating baseline compliance rules for new states.
    """

    source_rules = db.query(ComplianceRule).filter(
        ComplianceRule.state == source_state.upper(),
        ComplianceRule.is_active == True
    ).all()

    if not source_rules:
        raise HTTPException(
            status_code=404,
            detail=f"No rules found for state '{source_state}'"
        )

    cloned = []
    import random

    for rule in source_rules:
        rule_dict = {
            key: value for key, value in rule.__dict__.items()
            if key not in ['id', '_sa_instance_state', 'created_at', 'updated_at', 'parent_rule_id']
        }

        rule_dict['state'] = target_state.upper()
        rule_dict['rule_code'] = f"{target_state.upper()}-{rule.category.upper()}-{random.randint(100,999)}"
        rule_dict['created_by'] = agent_id
        rule_dict['is_draft'] = True
        rule_dict['version'] = 1
        rule_dict['parent_rule_id'] = None

        cloned_rule = ComplianceRule(**rule_dict)
        db.add(cloned_rule)
        cloned.append(rule_dict['rule_code'])

    db.commit()

    return {
        "status": "success",
        "source_state": source_state,
        "target_state": target_state,
        "rules_cloned": len(cloned),
        "cloned_rule_codes": cloned,
        "message": f"All rules marked as draft for review. Use /rules/{{id}}/publish to activate."
    }


# ========== VOICE-OPTIMIZED ENDPOINTS ==========

@router.post("/voice/add-rule", response_model=dict)
async def add_rule_voice(
    natural_language: str,
    state: str,
    category: Optional[str] = None,
    agent_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Voice: "Add a compliance rule for New York: All properties built before 1978 must have lead paint disclosure"

    Uses AI to parse natural language and create rule
    """

    generated_rule = await compliance_knowledge_service.generate_rule_with_ai(
        state=state.upper(),
        natural_language=natural_language,
        category=category
    )

    new_rule = ComplianceRule(
        **generated_rule,
        created_by=agent_id,
        is_draft=True
    )

    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)

    voice_confirmation = (
        f"I've created a new {generated_rule['category']} rule for {state}: "
        f"{generated_rule['title']}. "
        f"The rule is saved as a draft with code {generated_rule['rule_code']}. "
        "Would you like to review and publish it?"
    )

    return {
        "rule": ComplianceRuleResponse.from_orm(new_rule),
        "voice_confirmation": voice_confirmation
    }


@router.get("/voice/search-rules", response_model=dict)
def search_rules_voice(
    query: str,
    state: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Voice: "Show me all lead paint rules for New York"
    """

    search_query = db.query(ComplianceRule).filter(ComplianceRule.is_active == True)

    if state:
        search_query = search_query.filter(ComplianceRule.state == state.upper())

    # Search in title and description
    search_term = f"%{query}%"
    rules = search_query.filter(
        (ComplianceRule.title.ilike(search_term)) |
        (ComplianceRule.description.ilike(search_term))
    ).all()

    if not rules:
        voice_summary = f"No compliance rules found matching '{query}'"
        if state:
            voice_summary += f" for {state}"
    else:
        voice_summary = f"Found {len(rules)} rule{'s' if len(rules) != 1 else ''} matching '{query}'"
        if state:
            voice_summary += f" for {state}"
        voice_summary += ": "

        rule_titles = [r.title for r in rules[:3]]
        voice_summary += ", ".join(rule_titles)

        if len(rules) > 3:
            voice_summary += f", and {len(rules) - 3} more"

    return {
        "rules": [ComplianceRuleResponse.from_orm(r) for r in rules],
        "count": len(rules),
        "voice_summary": voice_summary
    }


# ========== RULE TEMPLATES ==========

@router.get("/templates", response_model=List[ComplianceRuleTemplateResponse])
def list_rule_templates(db: Session = Depends(get_db)):
    """Get pre-made rule templates for common compliance patterns"""

    return db.query(ComplianceRuleTemplate).all()


@router.post("/templates/{template_id}/use", response_model=ComplianceRuleResponse)
def create_rule_from_template(
    template_id: int,
    state: str,
    customization: dict = {},
    agent_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Create a new rule from a template.
    Fill in state-specific details.
    """

    template = db.query(ComplianceRuleTemplate).filter(
        ComplianceRuleTemplate.id == template_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Merge template with customization
    rule_data = {**template.template_json, **customization}
    rule_data['state'] = state.upper()
    rule_data['created_by'] = agent_id

    # Generate rule code if not provided
    if 'rule_code' not in rule_data or not rule_data['rule_code']:
        import random
        rule_data['rule_code'] = f"{state.upper()}-{rule_data['category'].upper()}-{random.randint(100, 999)}"

    new_rule = ComplianceRule(**rule_data)

    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)

    return new_rule
