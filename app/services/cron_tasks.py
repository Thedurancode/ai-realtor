"""Built-in task handlers for cron scheduler."""

import logging
from typing import Dict, Any
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


async def heartbeat_cycle_handler(db: Session, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Execute full heartbeat monitoring cycle.

    This is the main autonomous monitoring task that runs every 5 minutes.
    """
    from app.services.system_heartbeat_service import system_heartbeat_engine

    logger.info("Running heartbeat cycle...")

    # Run heartbeat cycle
    result = await system_heartbeat_engine.execute_cycle(db)

    logger.info(f"Heartbeat cycle complete: {result}")

    return result


async def portfolio_scan_handler(db: Session, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Scan portfolio for stale properties and issues.

    Runs every 5 minutes to check for:
    - Stale properties (no activity in 7+ days)
    - Contract deadlines approaching
    - Unsigned required contracts
    - High score properties with no action
    """
    from app.services.insights_service import insights_service

    logger.info("Running portfolio scan...")

    # Get all insights
    agent_id = metadata.get("agent_id")

    insights = insights_service.get_insights(
        db=db,
        property_id=None,
        agent_id=agent_id,
        priority=None
    )

    # Count by priority
    urgent = len([i for i in insights if i.get("priority") == "urgent"])
    high = len([i for i in insights if i.get("priority") == "high"])

    logger.info(f"Portfolio scan complete: {urgent} urgent, {high} high priority issues")

    return {
        "total_issues": len(insights),
        "urgent": urgent,
        "high": high,
        "insights": insights[:10]  # Return top 10
    }


async def market_intelligence_handler(db: Session, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Gather market intelligence and opportunities.

    Runs every 15 minutes to:
    - Scan for properties matching watchlist criteria
    - Detect market shifts (price changes, inventory changes)
    - Monitor competitive activity
    """
    from app.services.market_opportunity_scanner import market_opportunity_scanner
    from app.services.competitive_intelligence_service import competitive_intelligence_service

    logger.info("Running market intelligence...")

    agent_id = metadata.get("agent_id")
    city = metadata.get("city")
    state = metadata.get("state")

    results = {}

    # Scan for opportunities
    if agent_id:
        opportunities = market_opportunity_scanner.scan_market_opportunities(
            db=db,
            agent_id=agent_id,
            limit=10,
            min_score=70
        )
        results["opportunities_found"] = opportunities.get("total_scanned", 0)

    # Detect market shifts
    if city and state:
        shifts = await competitive_intelligence_service.detect_market_shifts(
            db=db,
            city=city,
            state=state,
            days_back=7
        )
        results["market_shifts"] = shifts.get("shifts_detected", 0)

    logger.info(f"Market intelligence complete: {results}")

    return results


async def relationship_health_handler(db: Session, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Score relationship health for all contacts.

    Runs every hour to:
    - Update health scores for all contacts
    - Detect cooling relationships
    - Flag contacts needing outreach
    """
    from app.services.relationship_intelligence_service import relationship_intelligence_service
    from app.models.contact import Contact

    logger.info("Running relationship health scoring...")

    # Get all contacts
    contacts = db.query(Contact).limit(100).all()  # Batch processing

    health_scores = []
    cooling_count = 0

    for contact in contacts:
        try:
            result = relationship_intelligence_service.score_relationship_health(
                db=db,
                contact_id=contact.id
            )

            if "error" not in result:
                health_scores.append({
                    "contact_id": contact.id,
                    "name": contact.name,
                    "health_score": result.get("health_score"),
                    "trend": result.get("trend")
                })

                # Check for cooling trend
                if result.get("trend") == "↓ decreasing":
                    cooling_count += 1

        except Exception as e:
            logger.warning(f"Failed to score contact {contact.id}: {e}")

    logger.info(
        f"Relationship health complete: "
        f"{len(health_scores)} scored, {cooling_count} cooling"
    )

    return {
        "total_scored": len(health_scores),
        "cooling_detected": cooling_count,
        "average_health": sum(s["health_score"] for s in health_scores) / len(health_scores) if health_scores else 0
    }


async def predictive_insights_handler(db: Session, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Generate predictive insights for all active properties.

    Runs every hour to:
    - Update closing probabilities
    - Re-score properties
    - Update follow-up queue rankings
    """
    from app.services.predictive_intelligence_service import predictive_intelligence_service
    from app.services.property_scoring_service import property_scoring_service
    from app.models.property import Property

    logger.info("Running predictive insights...")

    # Get active properties (not complete)
    active_properties = db.query(Property).filter(
        Property.status != "complete"
    ).limit(20).all()

    predictions = []
    scores_updated = 0

    for prop in active_properties:
        try:
            # Predict outcome
            prediction = predictive_intelligence_service.predict_property_outcome(
                db=db,
                property_id=prop.id
            )

            if "error" not in prediction:
                predictions.append({
                    "property_id": prop.id,
                    "closing_probability": prediction.get("closing_probability"),
                    "confidence": prediction.get("confidence")
                })

            # Re-score property
            score_result = property_scoring_service.score_property(
                db=db,
                property_id=prop.id,
                force_refresh=True
            )

            if "error" not in score_result:
                scores_updated += 1

        except Exception as e:
            logger.warning(f"Failed to analyze property {prop.id}: {e}")

    # Calculate average closing probability
    avg_probability = 0
    if predictions:
        avg_probability = sum(
            p["closing_probability"] for p in predictions
        ) / len(predictions)

    logger.info(
        f"Predictive insights complete: "
        f"{len(predictions)} predictions, {scores_updated} scores updated, "
        f"avg closing probability: {avg_probability:.1%}"
    )

    return {
        "predictions_generated": len(predictions),
        "scores_updated": scores_updated,
        "average_closing_probability": avg_probability,
        "high_probability_deals": len([
            p for p in predictions
            if p["closing_probability"] > 0.7
        ])
    }


async def transaction_deadline_handler(db: Session, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Check all active transactions for overdue or upcoming milestones.

    Runs every 30 minutes to:
    - Flag overdue milestones
    - Alert on milestones due within 48 hours
    - Create notifications for each alert
    - Optionally send SMS/email to assigned parties
    """
    from app.services.transaction_coordinator_service import transaction_coordinator
    from app.services.notification_service import notification_service
    from app.models.notification import NotificationType, NotificationPriority

    logger.info("Running transaction deadline check...")

    alerts = transaction_coordinator.check_deadlines(db)

    if not alerts:
        logger.info("Transaction deadline check: all clear, no alerts")
        return {"alerts": 0, "overdue": 0, "upcoming": 0, "notifications_created": 0}

    overdue = [a for a in alerts if a["type"] == "overdue"]
    upcoming = [a for a in alerts if a["type"] == "upcoming"]
    notifications_created = 0

    # Create notifications for each alert
    for alert in alerts:
        try:
            priority = NotificationPriority.URGENT if alert["type"] == "overdue" else NotificationPriority.HIGH
            notification_service.create_notification(
                db=db,
                notification_type=NotificationType.TRANSACTION_DEADLINE,
                title=alert["message"],
                message=f"Milestone: {alert['milestone']} | Transaction #{alert['transaction_id']} | Property #{alert['property_id']}",
                priority=priority,
                property_id=alert.get("property_id"),
                icon="🔴" if alert["type"] == "overdue" else "🟡",
                data=alert,
            )
            notifications_created += 1
        except Exception as e:
            logger.warning(f"Failed to create notification for alert: {e}")

    # Send SMS for overdue milestones via Telnyx (best-effort)
    sms_sent = 0
    if overdue:
        sms_sent = await _send_deadline_sms(overdue)

    # Send email summary for all alerts via Resend (best-effort)
    email_sent = await _send_deadline_email(alerts)

    logger.info(
        f"Transaction deadline check complete: "
        f"{len(overdue)} overdue, {len(upcoming)} upcoming, "
        f"{notifications_created} notifications created"
    )

    return {
        "alerts": len(alerts),
        "overdue": len(overdue),
        "upcoming": len(upcoming),
        "notifications_created": notifications_created,
        "sms_sent": sms_sent,
        "email_sent": email_sent,
        "details": alerts[:10],
    }


async def _send_deadline_sms(overdue_alerts: list) -> int:
    """Send SMS via Telnyx for overdue milestones."""
    import os
    import httpx

    api_key = os.getenv("TELNYX_API_KEY", "")
    owner_phone = os.getenv("OWNER_PHONE", "")
    from_phone = os.getenv("TELNYX_FROM_NUMBER", "")

    if not all([api_key, owner_phone, from_phone]):
        logger.debug("SMS skipped: TELNYX_API_KEY, OWNER_PHONE, or TELNYX_FROM_NUMBER not set")
        return 0

    body = f"TC Alert: {len(overdue_alerts)} overdue milestone(s)\n"
    for a in overdue_alerts[:5]:
        body += f"- {a['message']}\n"

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.telnyx.com/v2/messages",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"from": from_phone, "to": owner_phone, "text": body},
                timeout=10,
            )
            if resp.status_code in (200, 201, 202):
                logger.info(f"SMS sent to {owner_phone}: {len(overdue_alerts)} overdue alerts")
                return 1
            else:
                logger.warning(f"SMS failed ({resp.status_code}): {resp.text[:200]}")
                return 0
    except Exception as e:
        logger.debug(f"SMS delivery failed: {e}")
        return 0


async def _send_deadline_email(alerts: list) -> bool:
    """Send deadline summary email via Resend."""
    import os
    import httpx

    api_key = os.getenv("RESEND_API_KEY", "")
    owner_email = os.getenv("OWNER_EMAIL", "emprezarioinc@gmail.com")

    if not api_key:
        logger.debug("Email skipped: RESEND_API_KEY not set")
        return False

    overdue = [a for a in alerts if a["type"] == "overdue"]
    upcoming = [a for a in alerts if a["type"] == "upcoming"]

    html = "<h2>Transaction Deadline Alert</h2>"
    if overdue:
        html += "<h3 style='color:red'>Overdue</h3><ul>"
        for a in overdue:
            html += f"<li><strong>{a['milestone']}</strong> — {a['message']}</li>"
        html += "</ul>"
    if upcoming:
        html += "<h3 style='color:orange'>Due Soon</h3><ul>"
        for a in upcoming:
            html += f"<li><strong>{a['milestone']}</strong> — {a['message']}</li>"
        html += "</ul>"

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "from": "RealtorClaw <notifications@emprezario.com>",
                    "to": [owner_email],
                    "subject": f"TC Alert: {len(overdue)} overdue, {len(upcoming)} upcoming",
                    "html": html,
                },
                timeout=10,
            )
            if resp.status_code in (200, 201):
                logger.info(f"Deadline email sent to {owner_email}")
                return True
            else:
                logger.warning(f"Email failed ({resp.status_code}): {resp.text[:200]}")
                return False
    except Exception as e:
        logger.debug(f"Email delivery failed: {e}")
        return False


# Task handler registry
TASK_HANDLERS = {
    "heartbeat_cycle": heartbeat_cycle_handler,
    "portfolio_scan": portfolio_scan_handler,
    "market_intelligence": market_intelligence_handler,
    "relationship_health": relationship_health_handler,
    "predictive_insights": predictive_insights_handler,
    "transaction_deadlines": transaction_deadline_handler,
}
