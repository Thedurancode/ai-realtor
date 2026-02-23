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


# Task handler registry
TASK_HANDLERS = {
    "heartbeat_cycle": heartbeat_cycle_handler,
    "portfolio_scan": portfolio_scan_handler,
    "market_intelligence": market_intelligence_handler,
    "relationship_health": relationship_health_handler,
    "predictive_insights": predictive_insights_handler,
}
