"""
Compliance Check API - Run compliance checks on properties
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.database import get_db
from app.models.property import Property
from app.models.compliance_rule import ComplianceCheck, ComplianceViolation, ComplianceStatus
from app.schemas.compliance import (
    ComplianceCheckResponse,
    ComplianceCheckDetailResponse,
    ComplianceViolationResponse,
    ComplianceCheckVoiceRequest,
    ComplianceVoiceResponse,
)
from app.services.compliance_engine import compliance_engine
from app.utils.websocket import get_ws_manager

router = APIRouter(prefix="/compliance", tags=["compliance"])




# ========== RUN COMPLIANCE CHECKS ==========

@router.post("/properties/{property_id}/check", response_model=ComplianceCheckDetailResponse)
async def run_compliance_check(
    property_id: int,
    check_type: str = "full",  # full, disclosure_only, safety_only, zoning_only, environmental_only
    agent_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Run full compliance check on a property.
    Evaluates against all applicable state/local rules.

    Check types:
    - full: All rules
    - disclosure_only: Only disclosure requirements
    - safety_only: Only safety and building code rules
    - zoning_only: Only zoning rules
    - environmental_only: Only environmental rules
    """

    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    # Run compliance check
    check = await compliance_engine.run_compliance_check(
        db=db,
        property=property,
        check_type=check_type,
        agent_id=agent_id
    )

    # Send notification if check failed
    if check.status == ComplianceStatus.FAILED.value:
        try:
            from app.services.notification_service import notification_service
            manager = get_ws_manager()

            await notification_service.notify_compliance_failed(
                db=db,
                manager=manager,
                property_id=property.id,
                property_address=property.address,
                failed_count=check.failed_count,
                check_id=check.id,
                agent_id=property.agent_id
            )
        except:
            pass  # Don't fail if notification fails

    # Reload check with violations
    check = db.query(ComplianceCheck).options(
        joinedload(ComplianceCheck.violations).joinedload(ComplianceViolation.rule)
    ).filter(ComplianceCheck.id == check.id).first()

    return check


@router.post("/properties/{property_id}/quick-check", response_model=dict)
async def quick_compliance_check(
    property_id: int,
    agent_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Quick compliance check - returns summary without storing full check.
    Useful for pre-listing validation.
    """

    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    # Run check
    check = await compliance_engine.run_compliance_check(
        db=db,
        property=property,
        check_type="full",
        agent_id=agent_id
    )

    return {
        "property_id": property_id,
        "property_address": property.address,
        "status": check.status,
        "total_rules_checked": check.total_rules_checked,
        "passed": check.passed_count,
        "failed": check.failed_count,
        "warnings": check.warning_count,
        "summary": check.ai_summary,
        "is_ready_to_list": check.status == ComplianceStatus.PASSED.value,
        "check_id": check.id
    }


# ========== GET CHECK RESULTS ==========

@router.get("/properties/{property_id}/checks", response_model=List[ComplianceCheckResponse])
def get_property_compliance_history(
    property_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get all compliance checks run on a property"""

    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    checks = db.query(ComplianceCheck).filter(
        ComplianceCheck.property_id == property_id
    ).order_by(ComplianceCheck.created_at.desc()).limit(limit).all()

    return checks


@router.get("/properties/{property_id}/latest-check", response_model=ComplianceCheckDetailResponse)
def get_latest_compliance_check(
    property_id: int,
    db: Session = Depends(get_db)
):
    """Get the most recent compliance check for a property"""

    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    check = db.query(ComplianceCheck).options(
        joinedload(ComplianceCheck.violations).joinedload(ComplianceViolation.rule)
    ).filter(
        ComplianceCheck.property_id == property_id
    ).order_by(ComplianceCheck.created_at.desc()).first()

    if not check:
        raise HTTPException(
            status_code=404,
            detail="No compliance check found for this property. Run a check first."
        )

    return check


@router.get("/checks/{check_id}", response_model=ComplianceCheckDetailResponse)
def get_compliance_check_detail(
    check_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed compliance check with all violations"""

    check = db.query(ComplianceCheck).options(
        joinedload(ComplianceCheck.violations).joinedload(ComplianceViolation.rule)
    ).filter(ComplianceCheck.id == check_id).first()

    if not check:
        raise HTTPException(status_code=404, detail="Check not found")

    return check


@router.get("/checks/{check_id}/violations", response_model=List[ComplianceViolationResponse])
def get_check_violations(
    check_id: int,
    severity: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all violations for a compliance check.
    Optionally filter by severity.
    """

    check = db.query(ComplianceCheck).filter(ComplianceCheck.id == check_id).first()
    if not check:
        raise HTTPException(status_code=404, detail="Check not found")

    query = db.query(ComplianceViolation).options(
        joinedload(ComplianceViolation.rule)
    ).filter(ComplianceViolation.check_id == check_id)

    if severity:
        query = query.filter(ComplianceViolation.severity == severity)

    return query.all()


# ========== VIOLATION MANAGEMENT ==========

@router.post("/violations/{violation_id}/resolve")
def resolve_violation(
    violation_id: int,
    resolution_notes: str,
    db: Session = Depends(get_db)
):
    """Mark a violation as resolved"""

    violation = db.query(ComplianceViolation).filter(
        ComplianceViolation.id == violation_id
    ).first()

    if not violation:
        raise HTTPException(status_code=404, detail="Violation not found")

    from datetime import datetime
    violation.is_resolved = True
    violation.resolved_at = datetime.utcnow()
    violation.resolution_notes = resolution_notes

    db.commit()

    return {
        "status": "resolved",
        "violation_id": violation_id,
        "resolution_notes": resolution_notes
    }


@router.get("/violations/{violation_id}", response_model=ComplianceViolationResponse)
def get_violation_detail(
    violation_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific violation"""

    violation = db.query(ComplianceViolation).options(
        joinedload(ComplianceViolation.rule)
    ).filter(ComplianceViolation.id == violation_id).first()

    if not violation:
        raise HTTPException(status_code=404, detail="Violation not found")

    return violation


# ========== COMPLIANCE REPORTS ==========

@router.get("/properties/{property_id}/report", response_model=dict)
def get_compliance_report(
    property_id: int,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive compliance report for a property.
    Includes latest check, all violations, and recommendations.
    """

    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    # Get latest check
    latest_check = db.query(ComplianceCheck).options(
        joinedload(ComplianceCheck.violations).joinedload(ComplianceViolation.rule)
    ).filter(
        ComplianceCheck.property_id == property_id
    ).order_by(ComplianceCheck.created_at.desc()).first()

    if not latest_check:
        return {
            "property_id": property_id,
            "property_address": property.address,
            "has_been_checked": False,
            "message": "No compliance check has been run on this property yet."
        }

    # Group violations by severity
    violations_by_severity = {
        "critical": [],
        "high": [],
        "medium": [],
        "low": [],
        "info": []
    }

    for v in latest_check.violations:
        if not v.is_resolved:
            violations_by_severity[v.severity].append({
                "id": v.id,
                "rule_code": v.rule.rule_code,
                "rule_title": v.rule.title,
                "message": v.violation_message,
                "explanation": v.ai_explanation,
                "recommendation": v.recommendation,
                "estimated_fix_cost": v.rule.estimated_fix_cost,
                "estimated_fix_time_days": v.rule.estimated_fix_time_days
            })

    # Calculate total estimated fix cost and time
    total_fix_cost = sum(
        v.rule.estimated_fix_cost or 0
        for v in latest_check.violations
        if not v.is_resolved and v.rule.estimated_fix_cost
    )

    total_fix_time = max(
        (v.rule.estimated_fix_time_days or 0 for v in latest_check.violations if not v.is_resolved),
        default=0
    )

    return {
        "property_id": property_id,
        "property_address": property.address,
        "property_state": property.state,
        "check_date": latest_check.completed_at,
        "overall_status": latest_check.status,
        "is_ready_to_list": latest_check.status == ComplianceStatus.PASSED.value,
        "summary": latest_check.ai_summary,
        "statistics": {
            "total_rules_checked": latest_check.total_rules_checked,
            "passed": latest_check.passed_count,
            "failed": latest_check.failed_count,
            "warnings": latest_check.warning_count
        },
        "violations_by_severity": violations_by_severity,
        "estimated_total_fix_cost": total_fix_cost,
        "estimated_total_fix_time_days": total_fix_time,
        "check_id": latest_check.id
    }


# ========== VOICE-OPTIMIZED ENDPOINTS ==========

@router.post("/voice/check", response_model=ComplianceVoiceResponse)
async def run_compliance_check_voice(
    request: ComplianceCheckVoiceRequest,
    agent_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Voice-optimized compliance check.
    Example: "run compliance check on 141 throop"
    """

    # Find property by partial address
    query = request.address_query.lower()
    property = db.query(Property).filter(
        Property.address.ilike(f"%{query}%")
    ).first()

    if not property:
        raise HTTPException(
            status_code=404,
            detail=f"No property found matching '{request.address_query}'"
        )

    # Run compliance check
    check = await compliance_engine.run_compliance_check(
        db=db,
        property=property,
        check_type=request.check_type or "full",
        agent_id=agent_id
    )

    # Reload check with violations
    check = db.query(ComplianceCheck).options(
        joinedload(ComplianceCheck.violations).joinedload(ComplianceViolation.rule)
    ).filter(ComplianceCheck.id == check.id).first()

    # Build voice response
    if check.status == ComplianceStatus.PASSED.value:
        voice_confirmation = (
            f"Good news! {property.address} passed all compliance checks. "
            f"Evaluated {check.total_rules_checked} {property.state} regulations. "
            "The property is ready to list."
        )
    else:
        voice_confirmation = (
            f"Compliance check complete for {property.address}. "
            f"Found {check.failed_count} critical issue{'s' if check.failed_count != 1 else ''} "
        )
        if check.warning_count > 0:
            voice_confirmation += f"and {check.warning_count} warning{'s' if check.warning_count != 1 else ''}. "
        voice_confirmation += "Would you like me to read the details?"

    return ComplianceVoiceResponse(
        check=check,
        voice_confirmation=voice_confirmation,
        voice_summary=check.ai_summary or ""
    )


@router.get("/voice/issues", response_model=dict)
def get_compliance_issues_voice(
    address_query: str,
    db: Session = Depends(get_db)
):
    """
    Voice: "what are the compliance issues with 141 throop"
    """

    property = db.query(Property).filter(
        Property.address.ilike(f"%{address_query}%")
    ).first()

    if not property:
        raise HTTPException(
            status_code=404,
            detail=f"No property found matching '{address_query}'"
        )

    # Get most recent check
    check = db.query(ComplianceCheck).options(
        joinedload(ComplianceCheck.violations).joinedload(ComplianceViolation.rule)
    ).filter(
        ComplianceCheck.property_id == property.id
    ).order_by(ComplianceCheck.created_at.desc()).first()

    if not check:
        raise HTTPException(
            status_code=404,
            detail="No compliance check found. Run a check first."
        )

    # Build voice summary of issues
    violations = [v for v in check.violations if not v.is_resolved]

    if not violations:
        voice_summary = f"All compliance issues for {property.address} have been resolved!"
    else:
        voice_summary = f"Found {len(violations)} issue{'s' if len(violations) != 1 else ''} with {property.address}:\n\n"

        for i, v in enumerate(violations[:5], 1):
            voice_summary += f"{i}. {v.violation_message}. {v.ai_explanation}\n"

        if len(violations) > 5:
            voice_summary += f"\n... and {len(violations) - 5} more issues"

    return {
        "property_address": property.address,
        "check_id": check.id,
        "total_issues": len(violations),
        "violations": [ComplianceViolationResponse.from_orm(v) for v in violations],
        "voice_summary": voice_summary
    }


@router.get("/voice/status", response_model=dict)
def get_compliance_status_voice(
    address_query: str,
    db: Session = Depends(get_db)
):
    """
    Voice: "is 141 throop ready to list?"
    """

    property = db.query(Property).filter(
        Property.address.ilike(f"%{address_query}%")
    ).first()

    if not property:
        raise HTTPException(
            status_code=404,
            detail=f"No property found matching '{address_query}'"
        )

    # Get most recent check
    check = db.query(ComplianceCheck).filter(
        ComplianceCheck.property_id == property.id
    ).order_by(ComplianceCheck.created_at.desc()).first()

    if not check:
        voice_response = (
            f"{property.address} hasn't been checked for compliance yet. "
            "Would you like me to run a compliance check now?"
        )
        return {
            "property_address": property.address,
            "has_been_checked": False,
            "is_ready_to_list": None,
            "voice_response": voice_response
        }

    is_ready = check.status == ComplianceStatus.PASSED.value

    if is_ready:
        voice_response = (
            f"Yes! {property.address} is fully compliant and ready to list. "
            f"Last checked {check.completed_at.strftime('%B %d')}."
        )
    else:
        voice_response = (
            f"Not yet. {property.address} has {check.failed_count} compliance issue{'s' if check.failed_count != 1 else ''} "
            "that must be fixed before listing. "
            "Would you like me to read them?"
        )

    return {
        "property_address": property.address,
        "has_been_checked": True,
        "is_ready_to_list": is_ready,
        "check_status": check.status,
        "failed_count": check.failed_count,
        "warning_count": check.warning_count,
        "last_checked": check.completed_at,
        "voice_response": voice_response
    }
