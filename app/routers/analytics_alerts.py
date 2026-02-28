"""
Analytics Alert Router

API endpoints for managing analytics alert rules and notifications.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from app.database import get_db
from app.models.analytics_alert import (
    AnalyticsAlertRule,
    AnalyticsAlertTrigger,
    AlertType,
    AlertStatus,
    AlertOperator,
)
from app.services.analytics_alert_service import AnalyticsAlertService
from pydantic import BaseModel, EmailStr


router = APIRouter(prefix="/analytics/alerts", tags=["analytics-alerts"])


# Schemas
class AlertRuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    alert_type: AlertType
    metric_name: str
    metric_dimension: Optional[str] = None
    operator: AlertOperator
    threshold_value: Optional[int] = None
    threshold_percent: Optional[int] = None
    time_window_minutes: int = 60
    goal_target: Optional[int] = None
    goal_deadline: Optional[datetime] = None
    notification_channels: List[str] = ["email"]
    notification_cooldown_minutes: int = 60
    notification_recipients: Optional[dict] = None
    webhook_url: Optional[str] = None
    webhook_headers: Optional[dict] = None
    severity: str = "medium"
    tags: Optional[List[str]] = None


class AlertRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    threshold_value: Optional[int] = None
    threshold_percent: Optional[int] = None
    notification_channels: Optional[List[str]] = None
    notification_cooldown_minutes: Optional[int] = None
    severity: Optional[str] = None


class AlertRuleResponse(BaseModel):
    id: int
    agent_id: int
    name: str
    description: Optional[str]
    alert_type: AlertType
    metric_name: str
    operator: AlertOperator
    threshold_value: Optional[int]
    threshold_percent: Optional[int]
    time_window_minutes: int
    status: AlertStatus
    enabled: bool
    last_triggered_at: Optional[datetime]
    notification_channels: List[str]
    severity: str
    created_at: datetime

    class Config:
        from_attributes = True


class AlertTriggerResponse(BaseModel):
    id: int
    alert_rule_id: int
    status: AlertStatus
    metric_value: int
    threshold_value: int
    deviation_percent: Optional[int]
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


# Endpoints
@router.post("/rules", response_model=AlertRuleResponse)
def create_alert_rule(
    rule: AlertRuleCreate,
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Create a new analytics alert rule"""
    new_rule = AnalyticsAlertRule(
        agent_id=agent_id,
        **rule.model_dump()
    )
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    return new_rule


@router.get("/rules", response_model=List[AlertRuleResponse])
def list_alert_rules(
    agent_id: int,
    enabled_only: bool = False,
    db: Session = Depends(get_db)
):
    """List all alert rules for an agent"""
    query = db.query(AnalyticsAlertRule).filter(AnalyticsAlertRule.agent_id == agent_id)

    if enabled_only:
        query = query.filter(AnalyticsAlertRule.enabled == True)

    rules = query.order_by(AnalyticsAlertRule.created_at.desc()).all()
    return rules


@router.get("/rules/{rule_id}", response_model=AlertRuleResponse)
def get_alert_rule(rule_id: int, db: Session = Depends(get_db)):
    """Get a specific alert rule"""
    rule = db.query(AnalyticsAlertRule).filter(AnalyticsAlertRule.id == rule_id).first()

    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    return rule


@router.put("/rules/{rule_id}", response_model=AlertRuleResponse)
def update_alert_rule(
    rule_id: int,
    updates: AlertRuleUpdate,
    db: Session = Depends(get_db)
):
    """Update an alert rule"""
    rule = db.query(AnalyticsAlertRule).filter(AnalyticsAlertRule.id == rule_id).first()

    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)

    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/rules/{rule_id}")
def delete_alert_rule(rule_id: int, db: Session = Depends(get_db)):
    """Delete an alert rule"""
    rule = db.query(AnalyticsAlertRule).filter(AnalyticsAlertRule.id == rule_id).first()

    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    db.delete(rule)
    db.commit()
    return {"message": "Alert rule deleted"}


@router.post("/rules/{rule_id}/trigger")
def manually_trigger_alert(rule_id: int, db: Session = Depends(get_db)):
    """Manually trigger an alert rule (for testing)"""
    rule = db.query(AnalyticsAlertRule).filter(AnalyticsAlertRule.id == rule_id).first()

    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    service = AnalyticsAlertService(db)
    triggers = service.check_alert_rules(agent_id=rule.agent_id)

    if not triggers:
        return {"message": "Alert condition not met", "triggered": False}

    return {
        "message": "Alert triggered successfully",
        "triggered": True,
        "triggers": [t.id for t in triggers]
    }


@router.get("/rules/{rule_id}/history", response_model=List[AlertTriggerResponse])
def get_alert_history(
    rule_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get trigger history for an alert rule"""
    triggers = db.query(AnalyticsAlertTrigger).filter(
        AnalyticsAlertTrigger.alert_rule_id == rule_id
    ).order_by(AnalyticsAlertTrigger.created_at.desc()).limit(limit).all()

    return triggers


@router.post("/check")
def check_all_alerts(
    agent_id: Optional[int] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Check all alert rules and trigger if conditions are met.

    This is typically called by a background task/scheduler every few minutes.
    """
    service = AnalyticsAlertService(db)

    if background_tasks:
        # Run in background
        background_tasks.add_task(service.check_alert_rules, agent_id)
        return {"message": "Alert check started in background"}
    else:
        # Run synchronously
        triggers = service.check_alert_rules(agent_id)
        return {
            "message": f"Checked alerts, {len(triggers)} triggered",
            "triggered_count": len(triggers),
            "trigger_ids": [t.id for t in triggers]
        }


@router.get("/summaries/daily")
def get_daily_summary(agent_id: int, db: Session = Depends(get_db)):
    """Get daily analytics summary for notifications"""
    service = AnalyticsAlertService(db)
    summary = service.generate_daily_summary(agent_id)
    return summary


@router.get("/summaries/weekly")
def get_weekly_summary(agent_id: int, db: Session = Depends(get_db)):
    """Get weekly analytics summary for notifications"""
    service = AnalyticsAlertService(db)
    summary = service.generate_weekly_summary(agent_id)
    return summary


@router.post("/defaults")
def create_default_alerts(agent_id: int, db: Session = Depends(get_db)):
    """Create default alert rules for a new agent"""
    service = AnalyticsAlertService(db)
    rules = service.create_default_alerts(agent_id)
    return {
        "message": f"Created {len(rules)} default alert rules",
        "rules": [r.id for r in rules]
    }


@router.get("/triggers", response_model=List[AlertTriggerResponse])
def list_recent_triggers(
    agent_id: int,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List recent alert triggers for an agent"""
    triggers = db.query(AnalyticsAlertTrigger).join(
        AnalyticsAlertRule,
        AnalyticsAlertTrigger.alert_rule_id == AnalyticsAlertRule.id
    ).filter(
        AnalyticsAlertRule.agent_id == agent_id
    ).order_by(
        AnalyticsAlertTrigger.created_at.desc()
    ).limit(limit).all()

    return triggers


@router.put("/triggers/{trigger_id}/resolve")
def resolve_alert_trigger(
    trigger_id: int,
    resolution_note: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Mark an alert trigger as resolved"""
    trigger = db.query(AnalyticsAlertTrigger).filter(
        AnalyticsAlertTrigger.id == trigger_id
    ).first()

    if not trigger:
        raise HTTPException(status_code=404, detail="Alert trigger not found")

    trigger.status = AlertStatus.RESOLVED
    trigger.resolved_at = datetime.now(timezone.utc)
    trigger.resolution_note = resolution_note

    # Also update rule status
    rule = db.query(AnalyticsAlertRule).filter(
        AnalyticsAlertRule.id == trigger.alert_rule_id
    ).first()
    if rule:
        rule.status = AlertStatus.RESOLVED
        rule.last_resolved_at = datetime.now(timezone.utc)

    db.commit()
    return {"message": "Alert resolved"}
