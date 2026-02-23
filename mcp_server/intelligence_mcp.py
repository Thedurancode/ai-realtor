"""MCP tools for intelligence features - predictive, learning, opportunities, relationships, campaigns, negotiation, documents, competition, sequencing."""

from typing import Any, Optional
from datetime import datetime

from mcp.server.fastmcp import fastmcp
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.predictive_intelligence_service import predictive_intelligence_service
from app.services.learning_system_service import learning_system_service
from app.services.market_opportunity_scanner import market_opportunity_scanner
from app.services.relationship_intelligence_service import relationship_intelligence_service
from app.services.autonomous_campaign_manager import autonomous_campaign_manager
from app.services.negotiation_agent_service import negotiation_agent_service
from app.services.document_analyzer_service import document_analyzer_service
from app.services.competitive_intelligence_service import competitive_intelligence_service
from app.services.deal_sequencer_service import deal_sequencer_service
from app.models.deal_outcome import OutcomeStatus

mcp = fastmcp("AI Realtor Intelligence Tools")


# ── Predictive Intelligence Tools ──


@mcp.tool()
def predict_property_outcome(property_id: int) -> str:
    """Predict closing probability and recommend actions for a property.

    Args:
        property_id: Property to analyze

    Returns:
        Closing probability (0-100%), confidence, risk factors, strengths, and recommended actions.
    """
    db = SessionLocal()
    try:
        result = predictive_intelligence_service.predict_property_outcome(db, property_id)
        if "error" in result:
            return f"Error: {result['error']}"

        voice = result.get("voice_summary", "")
        return (
            f"{voice}\n"
            f"Closing Probability: {result['closing_probability']*100:.0f}%\n"
            f"Confidence: {result['confidence']}\n"
            f"Estimated Days to Close: {result['time_to_close_estimate_days']}"
        )
    finally:
        db.close()


@mcp.tool()
def recommend_next_action(property_id: int, context: Optional[str] = None) -> str:
    """Get AI-recommended next action for a property with reasoning.

    Args:
        property_id: Property to analyze
        context: Optional context (e.g., "offer_received", "inspection_complete")

    Returns:
        Recommended action, reasoning, priority, and expected impact.
    """
    db = SessionLocal()
    try:
        result = predictive_intelligence_service.recommend_next_action(db, property_id, context)
        if "error" in result:
            return f"Error: {result['error']}"

        return (
            f"{result['voice_summary']}\n"
            f"Action: {result['recommended_action']}\n"
            f"Priority: {result['priority']}\n"
            f"Expected Impact: {result['expected_impact']}"
        )
    finally:
        db.close()


@mcp.tool()
def batch_predict_outcomes(property_ids: Optional[list[int]] = None) -> str:
    """Predict outcomes for multiple properties, sorted by priority.

    Args:
        property_ids: Optional list of property IDs (scans all active if not provided)

    Returns:
        Prioritized list with lowest closing probabilities first.
    """
    db = SessionLocal()
    try:
        result = predictive_intelligence_service.batch_predict_outcomes(db, property_ids)
        return result.get("voice_summary", f"Analyzed {result.get('total_analyzed', 0)} properties")
    finally:
        db.close()


@mcp.tool()
def record_deal_outcome(
    property_id: int,
    status: str,
    final_sale_price: Optional[float] = None,
    outcome_reason: Optional[str] = None,
    lessons_learned: Optional[str] = None,
) -> str:
    """Record actual deal outcome for machine learning.

    Args:
        property_id: Property that closed
        status: "closed_won", "closed_lost", "withdrawn", or "stalled"
        final_sale_price: Final sale price (if sold)
        outcome_reason: Why did it succeed/fail?
        lessons_learned: Free-form insights for learning

    Returns:
        Confirmation that outcome was recorded.
    """
    db = SessionLocal()
    try:
        outcome_status = OutcomeStatus(status)
        result = learning_system_service.record_outcome(
            db, property_id, outcome_status, final_sale_price, outcome_reason, lessons_learned
        )
        if "error" in result:
            return f"Error: {result['error']}"

        return f"Recorded {status} outcome for property {property_id}. Learning system updated."
    finally:
        db.close()


@mcp.tool()
def get_agent_success_patterns(agent_id: int, period: str = "month") -> str:
    """Get agent's success patterns from historical performance.

    Args:
        agent_id: Agent to analyze
        period: "week", "month", "quarter", or "year"

    Returns:
        Best property types, cities, price ranges, average time to close, and success factors.
    """
    db = SessionLocal()
    try:
        result = learning_system_service.get_agent_success_patterns(db, agent_id, period)
        return result.get("voice_summary", f"Analyzed patterns for agent {agent_id}")
    finally:
        db.close()


@mcp.tool()
def get_prediction_accuracy(agent_id: Optional[int] = None, days: int = 30) -> str:
    """Evaluate prediction accuracy over time.

    Args:
        agent_id: Optional agent filter
        days: Number of days to look back

    Returns:
        Mean absolute error, directional accuracy, and confidence calibration.
    """
    db = SessionLocal()
    try:
        result = learning_system_service.evaluate_prediction_accuracy(db, agent_id, days)
        return result.get("voice_summary", "Accuracy evaluation complete")
    finally:
        db.close()


# ── Market Opportunity Scanner Tools ──


@mcp.tool()
def scan_market_opportunities(
    agent_id: int,
    limit: int = 10,
    min_score: float = 70,
    property_types: Optional[list[str]] = None,
    cities: Optional[list[str]] = None,
    max_price: Optional[float] = None,
) -> str:
    """Scan for opportunities matching agent's success patterns.

    Args:
        agent_id: Agent to scan for
        limit: Max opportunities to return
        min_score: Minimum deal score (0-100)
        property_types: Optional filter (e.g., ["house", "condo"])
        cities: Optional city filter
        max_price: Maximum price filter

    Returns:
        Top opportunities with match reasons and ROI estimates.
    """
    db = SessionLocal()
    try:
        result = market_opportunity_scanner.scan_market_opportunities(
            db, agent_id, limit, min_score, property_types, cities, max_price
        )
        return result.get("voice_summary", f"Found {result.get('opportunities_found', 0)} opportunities")
    finally:
        db.close()


@mcp.tool()
def detect_market_shifts(agent_id: int, cities: Optional[list[str]] = None) -> str:
    """Detect significant changes in market conditions.

    Args:
        agent_id: Agent to analyze for
        cities: Optional cities to monitor (uses watchlists if not provided)

    Returns:
        Price drops/surges, inventory shifts, and actionable alerts.
    """
    db = SessionLocal()
    try:
        result = market_opportunity_scanner.detect_market_shifts(db, agent_id, cities)
        return result.get("voice_summary", f"Detected {result.get('shifts_detected', 0)} market shifts")
    finally:
        db.close()


@mcp.tool()
def find_similar_properties(property_id: int, agent_id: Optional[int] = None, limit: int = 5) -> str:
    """Find similar properties for comparison.

    Args:
        property_id: Reference property
        agent_id: Optional agent filter
        limit: Max similar properties to return

    Returns:
        Similar properties with similarity scores and reasons.
    """
    db = SessionLocal()
    try:
        result = market_opportunity_scanner.find_similar_deals(db, property_id, agent_id, limit)
        return result.get("voice_summary", f"Found {len(result.get('similar_properties', []))} similar properties")
    finally:
        db.close()


# ── Relationship Intelligence Tools ──


@mcp.tool()
def score_relationship_health(contact_id: int) -> str:
    """Get relationship health score for a contact.

    Args:
        contact_id: Contact to analyze

    Returns:
        Health score (0-100), trend, communication frequency, responsiveness, and recommendations.
    """
    db = SessionLocal()
    try:
        result = relationship_intelligence_service.score_relationship_health(db, contact_id)
        if "error" in result:
            return f"Error: {result['error']}"
        return result.get("voice_summary", f"Relationship health: {result['health_score']:.0f}/100")
    finally:
        db.close()


@mcp.tool()
def predict_best_contact_method(contact_id: int, message_type: str = "check_in") -> str:
    """Predict the best contact method: phone, email, or text.

    Args:
        contact_id: Contact to analyze
        message_type: Type of message (e.g., "check_in", "offer_discussion")

    Returns:
        Recommended method with reasoning and success rates.
    """
    db = SessionLocal()
    try:
        result = relationship_intelligence_service.predict_best_contact_method(db, contact_id, message_type)
        if "error" in result:
            return f"Error: {result['error']}"
        return result.get("voice_summary", f"Recommend {result['recommended_method']}")
    finally:
        db.close()


@mcp.tool()
def analyze_contact_sentiment(contact_id: int, days: int = 30) -> str:
    """Analyze sentiment trend for a contact over time.

    Args:
        contact_id: Contact to analyze
        days: Number of days to look back

    Returns:
        Sentiment trend, average score, and recent interactions.
    """
    db = SessionLocal()
    try:
        result = relationship_intelligence_service.analyze_contact_sentiment(db, contact_id, days)
        if "error" in result:
            return f"Error: {result['error']}"
        return result.get("voice_summary", f"Sentiment: {result['average_sentiment']:.1f}")
    finally:
        db.close()


# ── Autonomous Campaign Manager Tools ──


@mcp.tool()
def optimize_campaign_parameters(campaign_id: int) -> str:
    """Auto-adjust call time, message, targeting based on performance.

    Args:
        campaign_id: Campaign to optimize

    Returns:
        Best calling times, winning messages, and targeting insights.
    """
    db = SessionLocal()
    try:
        result = autonomous_campaign_manager.optimize_campaign_parameters(db, campaign_id)
        if "error" in result:
            return f"Error: {result['error']}"
        return f"Campaign {campaign_id} optimization complete. {len(result.get('recommended_adjustments', []))} adjustments identified."
    finally:
        db.close()


@mcp.tool()
def get_campaign_roi(campaign_id: int) -> str:
    """Calculate ROI of a campaign.

    Args:
        campaign_id: Campaign to analyze

    Returns:
        Cost, outcomes, success rate, and ROI metrics.
    """
    db = SessionLocal()
    try:
        result = autonomous_campaign_manager.get_campaign_roi(db, campaign_id)
        if "error" in result:
            return f"Error: {result['error']}"
        return result.get("voice_summary", f"Campaign ROI: {result['success_rate']:.0f}% success rate")
    finally:
        db.close()


# ── Negotiation Agent Tools ──


@mcp.tool()
def analyze_offer(
    property_id: int,
    offer_amount: float,
    buyer_concessions: Optional[list[str]] = None,
    contingencies: Optional[list[str]] = None,
) -> str:
    """Analyze an offer against deal metrics and market data.

    Args:
        property_id: Property for the offer
        offer_amount: Offer amount in dollars
        buyer_concessions: Optional concessions from buyer
        contingencies: Optional contingencies

    Returns:
        Acceptance probability, counter-offer strategy, talking points, and walkaway price.
    """
    db = SessionLocal()
    try:
        result = negotiation_agent_service.analyze_offer(
            db, property_id, offer_amount, buyer_concessions, contingencies
        )
        if "error" in result:
            return f"Error: {result['error']}"
        return (
            f"{result['voice_summary']}\n"
            f"Acceptance Probability: {result['acceptance_probability']*100:.0f}%\n"
            f"Recommendation: {result['recommendation']}\n"
            f"Walkaway Price: ${result.get('walkaway_price', 0):,.0f}"
        )
    finally:
        db.close()


@mcp.tool()
def generate_counter_offer(
    property_id: int, their_offer: float, counter_amount: float, reason: Optional[str] = None
) -> str:
    """Generate persuasive counter-offer letter with market justification.

    Args:
        property_id: Property for counter-offer
        their_offer: Their offer amount
        counter_amount: Your counter-offer amount
        reason: Optional reason for counter

    Returns:
        Counter-offer letter with talking points.
    """
    db = SessionLocal()
    try:
        result = negotiation_agent_service.generate_counter_offer(
            db, property_id, their_offer, counter_amount, reason
        )
        if "error" in result:
            return f"Error: {result['error']}"
        return (
            f"{result['voice_summary']}\n\n"
            f"COUNTER-OFFER LETTER:\n{result['counter_offer_letter']}"
        )
    finally:
        db.close()


@mcp.tool()
def suggest_offer_price(property_id: int, aggressiveness: str = "moderate") -> str:
    """Suggest an optimal offer price based on market analysis.

    Args:
        property_id: Property to analyze
        aggressiveness: "conservative", "moderate", or "aggressive"

    Returns:
        Suggested offer with range and justification.
    """
    db = SessionLocal()
    try:
        result = negotiation_agent_service.suggest_offer_price(db, property_id, aggressiveness)
        if "error" in result:
            return f"Error: {result['error']}"
        return (
            f"{result['voice_summary']}\n"
            f"Suggested Offer: ${result['suggested_offer']:,.0f}\n"
            f"Range: ${result['range']['min']:,.0f} - ${result['range']['max']:,.0f}"
        )
    finally:
        db.close()


# ── Document Analysis Tools ──


@mcp.tool()
def analyze_inspection_report(property_id: int, document_text: str) -> str:
    """Extract key issues from inspection report using NLP.

    Args:
        property_id: Property for the inspection
        document_text: Text content of inspection report

    Returns:
        Critical issues, repair estimates, negotiation leverage, and deal killers.
    """
    db = SessionLocal()
    try:
        result = document_analyzer_service.analyze_inspection_report(db, property_id, document_text, create_note=True)
        if "error" in result:
            return f"Error: {result['error']}"
        return (
            f"{result['voice_summary']}\n"
            f"Critical Issues: {len(result['critical_issues'])}\n"
            f"Total Repair Estimate: ${result['total_repair_estimate']:,.0f}"
        )
    finally:
        db.close()


@mcp.tool()
def extract_contract_terms(property_id: int, contract_text: str) -> str:
    """Extract key terms from a contract document.

    Args:
        property_id: Property for the contract
        contract_text: Text content of contract

    Returns:
        Parties, key dates, financial terms, contingencies, and obligations.
    """
    db = SessionLocal()
    try:
        result = document_analyzer_service.extract_contract_terms(db, property_id, contract_text)
        if "error" in result:
            return f"Error: {result['error']}"
        return result.get("voice_summary", "Contract terms extracted")
    finally:
        db.close()


# ── Competitive Intelligence Tools ──


@mcp.tool()
def analyze_market_competition(city: str, state: str, property_type: Optional[str] = None) -> str:
    """Analyze competing agents in a specific market.

    Args:
        city: City to analyze
        state: State abbreviation
        property_type: Optional property type filter

    Returns:
        Most active agents, fastest closers, highest spenders, and winning bid patterns.
    """
    db = SessionLocal()
    try:
        result = competitive_intelligence_service.analyze_market_competition(
            db, city, state, property_type
        )
        return result.get("voice_summary", f"Analyzed competition in {city}, {state}")
    finally:
        db.close()


@mcp.tool()
def detect_competitive_activity(property_id: int) -> str:
    """Alert if competition is interested in the same property.

    Args:
        property_id: Property to check

    Returns:
        Competitive activity alerts with urgency and recommended actions.
    """
    db = SessionLocal()
    try:
        result = competitive_intelligence_service.detect_competitive_activity(db, property_id)
        if "error" in result:
            return f"Error: {result['error']}"
        return result.get("voice_summary", "No competitive activity detected")
    finally:
        db.close()


@mcp.tool()
def get_market_saturation(city: str, state: str, property_type: Optional[str] = None) -> str:
    """Analyze market saturation - inventory levels and demand.

    Args:
        city: City to analyze
        state: State abbreviation
        property_type: Optional property type filter

    Returns:
        Inventory level, days on market, price trend, and market health.
    """
    db = SessionLocal()
    try:
        result = competitive_intelligence_service.get_market_saturation(db, city, state, property_type)
        return result.get(
            "voice_summary",
            f"Market saturation for {city}, {state}: {result['inventory_level']} inventory, {result['price_trend']} prices",
        )
    finally:
        db.close()


# ── Deal Sequencer Tools ──


@mcp.tool()
def sequence_1031_exchange(
    sale_property_id: int, target_criteria: dict, agent_id: int
) -> str:
    """Orchestrate a 1031 exchange with timeline management.

    Args:
        sale_property_id: Property being sold
        target_criteria: Criteria for replacement properties (cities, types, etc.)
        agent_id: Agent orchestrating the exchange

    Returns:
        1031 exchange phases, timeline, deadlines, and replacement candidates.
    """
    db = SessionLocal()
    try:
        result = deal_sequencer_service.sequence_1031_exchange(
            db, sale_property_id, target_criteria, agent_id
        )
        if "error" in result:
            return f"Error: {result['error']}"
        return result.get("voice_summary", "1031 exchange sequenced with automated reminders")
    finally:
        db.close()


@mcp.tool()
def sequence_portfolio_acquisition(
    property_ids: list[int], agent_id: int, strategy: str = "parallel"
) -> str:
    """Orchestrate buying multiple properties with optimal ordering.

    Args:
        property_ids: Properties to acquire
        agent_id: Agent orchestrating
        strategy: "parallel" (all at once) or "sequential" (one by one)

    Returns:
        Acquisition sequence with timeline, contingencies, and parallel actions.
    """
    db = SessionLocal()
    try:
        result = deal_sequencer_service.sequence_portfolio_acquisition(
            db, property_ids, agent_id, strategy
        )
        if "error" in result:
            return f"Error: {result['error']}"
        return result.get(
            "voice_summary",
            f"Acquisition sequenced: {len(property_ids)} properties {strategy} for ${result['total_investment']:,.0f}",
        )
    finally:
        db.close()


@mcp.tool()
def sequence_sell_and_buy(
    sale_property_id: int, purchase_property_id: int, contingency_type: str = "sale_contingent"
) -> str:
    """Orchestrate a sale-and-buy transaction with contingencies.

    Args:
        sale_property_id: Property to sell
        purchase_property_id: Property to buy
        contingency_type: "sale_contingent" or "buy_contingent"

    Returns:
        Transaction sequence with timeline and contingency management.
    """
    db = SessionLocal()
    try:
        result = deal_sequencer_service.sequence_sell_and_buy(
            db, sale_property_id, purchase_property_id, contingency_type
        )
        if "error" in result:
            return f"Error: {result['error']}"
        return result.get("voice_summary", "Sell-and-buy transaction sequenced")
    finally:
        db.close()
