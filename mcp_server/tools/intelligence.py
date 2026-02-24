"""Intelligence tools module - registers all intelligence MCP tools."""

from mcp.types import Tool, TextContent
from ..server import register_tool
from typing import Optional
from app.database import SessionLocal
from app.services.predictive_intelligence_service import predictive_intelligence_service
from app.services.learning_system_service import learning_system_service
from app.services.market_opportunity_scanner import market_opportunity_scanner
from app.services.relationship_intelligence_service import relationship_intelligence_service
from app.services.negotiation_agent_service import negotiation_agent_service
from app.services.document_analyzer_service import document_analyzer_service
from app.services.competitive_intelligence_service import competitive_intelligence_service
from app.services.deal_sequencer_service import deal_sequencer_service
from app.models.deal_outcome import OutcomeStatus


# ── Async Handlers ──

async def handle_predict_property_outcome(arguments: dict) -> list[TextContent]:
    property_id = arguments["property_id"]
    db = SessionLocal()
    try:
        result = predictive_intelligence_service.predict_property_outcome(db, property_id)
        if "error" in result:
            return [TextContent(type="text", text=f"Error: {result['error']}")]
        return [TextContent(type="text", text=result.get("voice_summary", f"Closing Probability: {result['closing_probability']*100:.0f}%"))]
    finally:
        db.close()


async def handle_recommend_next_action(arguments: dict) -> list[TextContent]:
    property_id = arguments["property_id"]
    context = arguments.get("context")
    db = SessionLocal()
    try:
        result = predictive_intelligence_service.recommend_next_action(db, property_id, context)
        if "error" in result:
            return [TextContent(type="text", text=f"Error: {result['error']}")]
        return [TextContent(type="text", text=result.get("voice_summary", f"Action: {result['recommended_action']}, Priority: {result['priority']}"))]
    finally:
        db.close()


async def handle_batch_predict_outcomes(arguments: dict) -> list[TextContent]:
    property_ids = arguments.get("property_ids")
    db = SessionLocal()
    try:
        result = predictive_intelligence_service.batch_predict_outcomes(db, property_ids)
        return [TextContent(type="text", text=result.get("voice_summary", f"Analyzed {result.get('total_analyzed', 0)} properties"))]
    finally:
        db.close()


async def handle_record_deal_outcome(arguments: dict) -> list[TextContent]:
    property_id = arguments["property_id"]
    status = arguments["status"]
    final_sale_price = arguments.get("final_sale_price")
    outcome_reason = arguments.get("outcome_reason")
    lessons_learned = arguments.get("lessons_learned")
    db = SessionLocal()
    try:
        outcome_status = OutcomeStatus(status)
        result = learning_system_service.record_outcome(db, property_id, outcome_status, final_sale_price, outcome_reason, lessons_learned)
        if "error" in result:
            return [TextContent(type="text", text=f"Error: {result['error']}")]
        return [TextContent(type="text", text=f"Recorded {status} outcome for property {property_id}. Learning system updated.")]
    finally:
        db.close()


async def handle_get_agent_success_patterns(arguments: dict) -> list[TextContent]:
    agent_id = arguments["agent_id"]
    period = arguments.get("period", "month")
    db = SessionLocal()
    try:
        result = learning_system_service.get_agent_success_patterns(db, agent_id, period)
        return [TextContent(type="text", text=result.get("voice_summary", f"Analyzed patterns for agent {agent_id}"))]
    finally:
        db.close()


async def handle_scan_market_opportunities(arguments: dict) -> list[TextContent]:
    agent_id = arguments["agent_id"]
    limit = arguments.get("limit", 10)
    min_score = arguments.get("min_score", 70)
    property_types = arguments.get("property_types")
    cities = arguments.get("cities")
    max_price = arguments.get("max_price")
    db = SessionLocal()
    try:
        result = market_opportunity_scanner.scan_market_opportunities(db, agent_id, limit, min_score, property_types, cities, max_price)
        return [TextContent(type="text", text=result.get("voice_summary", f"Found {result.get('opportunities_found', 0)} opportunities"))]
    finally:
        db.close()


async def handle_detect_market_shifts(arguments: dict) -> list[TextContent]:
    agent_id = arguments["agent_id"]
    cities = arguments.get("cities")
    db = SessionLocal()
    try:
        result = market_opportunity_scanner.detect_market_shifts(db, agent_id, cities)
        return [TextContent(type="text", text=result.get("voice_summary", f"Detected {result.get('shifts_detected', 0)} market shifts"))]
    finally:
        db.close()


async def handle_find_similar_properties_intel(arguments: dict) -> list[TextContent]:
    property_id = arguments["property_id"]
    agent_id = arguments.get("agent_id")
    limit = arguments.get("limit", 5)
    db = SessionLocal()
    try:
        result = market_opportunity_scanner.find_similar_deals(db, property_id, agent_id, limit)
        similar_count = len(result.get("similar_properties", []))
        return [TextContent(type="text", text=result.get("voice_summary", f"Found {similar_count} similar properties"))]
    finally:
        db.close()


async def handle_score_relationship_health(arguments: dict) -> list[TextContent]:
    contact_id = arguments["contact_id"]
    db = SessionLocal()
    try:
        result = relationship_intelligence_service.score_relationship_health(db, contact_id)
        if "error" in result:
            return [TextContent(type="text", text=f"Error: {result['error']}")]
        return [TextContent(type="text", text=result.get("voice_summary", f"Relationship health: {result['health_score']:.0f}/100"))]
    finally:
        db.close()


async def handle_predict_best_contact_method(arguments: dict) -> list[TextContent]:
    contact_id = arguments["contact_id"]
    message_type = arguments.get("message_type", "check_in")
    db = SessionLocal()
    try:
        result = relationship_intelligence_service.predict_best_contact_method(db, contact_id, message_type)
        if "error" in result:
            return [TextContent(type="text", text=f"Error: {result['error']}")]
        return [TextContent(type="text", text=result.get("voice_summary", f"Recommend {result['recommended_method']}"))]
    finally:
        db.close()


async def handle_analyze_offer(arguments: dict) -> list[TextContent]:
    property_id = arguments["property_id"]
    offer_amount = arguments["offer_amount"]
    buyer_concessions = arguments.get("buyer_concessions")
    contingencies = arguments.get("contingencies")
    db = SessionLocal()
    try:
        result = negotiation_agent_service.analyze_offer(db, property_id, offer_amount, buyer_concessions, contingencies)
        if "error" in result:
            return [TextContent(type="text", text=f"Error: {result['error']}")]
        return [TextContent(type="text", text=f"{result['voice_summary']} Recommendation: {result['recommendation']}, Walkaway: ${result.get('walkaway_price', 0):,.0f}")]
    finally:
        db.close()


async def handle_generate_counter_offer(arguments: dict) -> list[TextContent]:
    property_id = arguments["property_id"]
    their_offer = arguments["their_offer"]
    counter_amount = arguments["counter_amount"]
    reason = arguments.get("reason")
    db = SessionLocal()
    try:
        result = negotiation_agent_service.generate_counter_offer(db, property_id, their_offer, counter_amount, reason)
        if "error" in result:
            return [TextContent(type="text", text=f"Error: {result['error']}")]
        return [TextContent(type="text", text=f"{result['voice_summary']}\n\n{result['counter_offer_letter']}")]
    finally:
        db.close()


async def handle_suggest_offer_price(arguments: dict) -> list[TextContent]:
    property_id = arguments["property_id"]
    aggressiveness = arguments.get("aggressiveness", "moderate")
    db = SessionLocal()
    try:
        result = negotiation_agent_service.suggest_offer_price(db, property_id, aggressiveness)
        if "error" in result:
            return [TextContent(type="text", text=f"Error: {result['error']}")]
        return [TextContent(type="text", text=f"{result['voice_summary']} Suggested: ${result['suggested_offer']:,.0f}")]
    finally:
        db.close()


async def handle_analyze_inspection_report(arguments: dict) -> list[TextContent]:
    property_id = arguments["property_id"]
    document_text = arguments["document_text"]
    db = SessionLocal()
    try:
        result = document_analyzer_service.analyze_inspection_report(db, property_id, document_text, create_note=True)
        if "error" in result:
            return [TextContent(type="text", text=f"Error: {result['error']}")]
        return [TextContent(type="text", text=f"{result['voice_summary']} Critical Issues: {len(result['critical_issues'])}, Repairs: ${result['total_repair_estimate']:,.0f}")]
    finally:
        db.close()


async def handle_extract_contract_terms(arguments: dict) -> list[TextContent]:
    property_id = arguments["property_id"]
    contract_text = arguments["contract_text"]
    db = SessionLocal()
    try:
        result = document_analyzer_service.extract_contract_terms(db, property_id, contract_text)
        if "error" in result:
            return [TextContent(type="text", text=f"Error: {result['error']}")]
        return [TextContent(type="text", text=result.get("voice_summary", "Contract terms extracted successfully"))]
    finally:
        db.close()


async def handle_analyze_market_competition(arguments: dict) -> list[TextContent]:
    city = arguments["city"]
    state = arguments["state"]
    property_type = arguments.get("property_type")
    db = SessionLocal()
    try:
        result = competitive_intelligence_service.analyze_market_competition(db, city, state, property_type)
        return [TextContent(type="text", text=result.get("voice_summary", f"Analyzed competition in {city}, {state}"))]
    finally:
        db.close()


async def handle_detect_competitive_activity(arguments: dict) -> list[TextContent]:
    property_id = arguments["property_id"]
    db = SessionLocal()
    try:
        result = competitive_intelligence_service.detect_competitive_activity(db, property_id)
        if "error" in result:
            return [TextContent(type="text", text=f"Error: {result['error']}")]
        return [TextContent(type="text", text=result.get("voice_summary", "No competitive activity detected"))]
    finally:
        db.close()


async def handle_get_market_saturation(arguments: dict) -> list[TextContent]:
    city = arguments["city"]
    state = arguments["state"]
    property_type = arguments.get("property_type")
    db = SessionLocal()
    try:
        result = competitive_intelligence_service.get_market_saturation(db, city, state, property_type)
        return [TextContent(type="text", text=result.get("voice_summary", f"Market: {result['inventory_level']} inventory, {result['price_trend']} prices"))]
    finally:
        db.close()


async def handle_sequence_1031_exchange(arguments: dict) -> list[TextContent]:
    sale_property_id = arguments["sale_property_id"]
    target_criteria = arguments["target_criteria"]
    agent_id = arguments["agent_id"]
    db = SessionLocal()
    try:
        result = deal_sequencer_service.sequence_1031_exchange(db, sale_property_id, target_criteria, agent_id)
        if "error" in result:
            return [TextContent(type="text", text=f"Error: {result['error']}")]
        return [TextContent(type="text", text=result.get("voice_summary", "1031 exchange sequenced with automated reminders"))]
    finally:
        db.close()


async def handle_sequence_portfolio_acquisition(arguments: dict) -> list[TextContent]:
    property_ids = arguments["property_ids"]
    agent_id = arguments["agent_id"]
    strategy = arguments.get("strategy", "parallel")
    db = SessionLocal()
    try:
        result = deal_sequencer_service.sequence_portfolio_acquisition(db, property_ids, agent_id, strategy)
        if "error" in result:
            return [TextContent(type="text", text=f"Error: {result['error']}")]
        return [TextContent(type="text", text=f"{result['voice_summary']} Total: ${result['total_investment']:,.0f}, Timeline: {result['estimated_timeline_days']} days")]
    finally:
        db.close()


async def handle_sequence_sell_and_buy(arguments: dict) -> list[TextContent]:
    sale_property_id = arguments["sale_property_id"]
    purchase_property_id = arguments["purchase_property_id"]
    contingency_type = arguments.get("contingency_type", "sale_contingent")
    db = SessionLocal()
    try:
        result = deal_sequencer_service.sequence_sell_and_buy(db, sale_property_id, purchase_property_id, contingency_type)
        if "error" in result:
            return [TextContent(type="text", text=f"Error: {result['error']}")]
        return [TextContent(type="text", text=result.get("voice_summary", "Sell-and-buy transaction sequenced"))]
    finally:
        db.close()


# ── Tool Registration ──

register_tool(
    Tool(
        name="predict_property_outcome",
        description="Predict closing probability and recommend actions for a property. Returns closing probability (0-100%), confidence, risk factors, strengths, and recommended actions.",
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {"type": "integer", "description": "Property to analyze"}
            },
            "required": ["property_id"]
        }
    ),
    handle_predict_property_outcome
)

register_tool(
    Tool(
        name="recommend_next_action",
        description="Get AI-recommended next action for a property with reasoning. Returns recommended action, reasoning, priority, and expected impact.",
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {"type": "integer"},
                "context": {"type": "string", "description": "Optional context (e.g., offer_received, inspection_complete)"}
            },
            "required": ["property_id"]
        }
    ),
    handle_recommend_next_action
)

register_tool(
    Tool(
        name="batch_predict_outcomes",
        description="Predict outcomes for multiple properties, sorted by priority (lowest probability first)",
        inputSchema={
            "type": "object",
            "properties": {
                "property_ids": {"type": "array", "items": {"type": "integer"}, "description": "Optional list of property IDs"}
            }
        }
    ),
    handle_batch_predict_outcomes
)

register_tool(
    Tool(
        name="record_deal_outcome",
        description="Record actual deal outcome for machine learning. Status: closed_won, closed_lost, withdrawn, or stalled",
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {"type": "integer"},
                "status": {"type": "string", "enum": ["closed_won", "closed_lost", "withdrawn", "stalled"]},
                "final_sale_price": {"type": "number"},
                "outcome_reason": {"type": "string"},
                "lessons_learned": {"type": "string"}
            },
            "required": ["property_id", "status"]
        }
    ),
    handle_record_deal_outcome
)

register_tool(
    Tool(
        name="get_agent_success_patterns",
        description="Get agent's success patterns from historical performance. Returns best property types, cities, price ranges, and success factors.",
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {"type": "integer"},
                "period": {"type": "string", "enum": ["week", "month", "quarter", "year"], "default": "month"}
            },
            "required": ["agent_id"]
        }
    ),
    handle_get_agent_success_patterns
)

register_tool(
    Tool(
        name="scan_market_opportunities",
        description="Scan for opportunities matching agent's success patterns. Returns top opportunities with match reasons and ROI estimates.",
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {"type": "integer"},
                "limit": {"type": "integer", "default": 10},
                "min_score": {"type": "number", "default": 70},
                "property_types": {"type": "array", "items": {"type": "string"}},
                "cities": {"type": "array", "items": {"type": "string"}},
                "max_price": {"type": "number"}
            },
            "required": ["agent_id"]
        }
    ),
    handle_scan_market_opportunities
)

register_tool(
    Tool(
        name="detect_market_shifts",
        description="Detect significant changes in market conditions (price drops/surges >10%)",
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {"type": "integer"},
                "cities": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["agent_id"]
        }
    ),
    handle_detect_market_shifts
)

register_tool(
    Tool(
        name="find_similar_properties",
        description="Find similar properties for comparison. Returns similar properties with similarity scores.",
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {"type": "integer"},
                "agent_id": {"type": "integer"},
                "limit": {"type": "integer", "default": 5}
            },
            "required": ["property_id"]
        }
    ),
    handle_find_similar_properties_intel
)

register_tool(
    Tool(
        name="score_relationship_health",
        description="Get relationship health score for a contact (0-100). Returns health score, trend, and recommendations.",
        inputSchema={
            "type": "object",
            "properties": {
                "contact_id": {"type": "integer"}
            },
            "required": ["contact_id"]
        }
    ),
    handle_score_relationship_health
)

register_tool(
    Tool(
        name="predict_best_contact_method",
        description="Predict the best contact method: phone, email, or text. Returns recommendation with reasoning.",
        inputSchema={
            "type": "object",
            "properties": {
                "contact_id": {"type": "integer"},
                "message_type": {"type": "string", "default": "check_in"}
            },
            "required": ["contact_id"]
        }
    ),
    handle_predict_best_contact_method
)

register_tool(
    Tool(
        name="analyze_offer",
        description="Analyze an offer against deal metrics and market data. Returns acceptance probability, counter strategy, and walkaway price.",
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {"type": "integer"},
                "offer_amount": {"type": "number"},
                "buyer_concessions": {"type": "array", "items": {"type": "string"}},
                "contingencies": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["property_id", "offer_amount"]
        }
    ),
    handle_analyze_offer
)

register_tool(
    Tool(
        name="generate_counter_offer",
        description="Generate persuasive counter-offer letter with market justification",
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {"type": "integer"},
                "their_offer": {"type": "number"},
                "counter_amount": {"type": "number"},
                "reason": {"type": "string"}
            },
            "required": ["property_id", "their_offer", "counter_amount"]
        }
    ),
    handle_generate_counter_offer
)

register_tool(
    Tool(
        name="suggest_offer_price",
        description="Suggest an optimal offer price based on market analysis (conservative/moderate/aggressive)",
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {"type": "integer"},
                "aggressiveness": {"type": "string", "enum": ["conservative", "moderate", "aggressive"], "default": "moderate"}
            },
            "required": ["property_id"]
        }
    ),
    handle_suggest_offer_price
)

register_tool(
    Tool(
        name="analyze_inspection_report",
        description="Extract key issues from inspection report using NLP. Returns critical issues, repair estimates, and deal killers.",
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {"type": "integer"},
                "document_text": {"type": "string"}
            },
            "required": ["property_id", "document_text"]
        }
    ),
    handle_analyze_inspection_report
)

register_tool(
    Tool(
        name="extract_contract_terms",
        description="Extract key terms from a contract document. Returns parties, dates, financial terms, and contingencies.",
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {"type": "integer"},
                "contract_text": {"type": "string"}
            },
            "required": ["property_id", "contract_text"]
        }
    ),
    handle_extract_contract_terms
)

register_tool(
    Tool(
        name="analyze_market_competition",
        description="Analyze competing agents in a specific market. Returns most active agents, fastest closers, and winning bid patterns.",
        inputSchema={
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "state": {"type": "string"},
                "property_type": {"type": "string"}
            },
            "required": ["city", "state"]
        }
    ),
    handle_analyze_market_competition
)

register_tool(
    Tool(
        name="detect_competitive_activity",
        description="Alert if competition is interested in the same property. Returns activity alerts with urgency.",
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {"type": "integer"}
            },
            "required": ["property_id"]
        }
    ),
    handle_detect_competitive_activity
)

register_tool(
    Tool(
        name="get_market_saturation",
        description="Analyze market saturation - inventory levels and demand. Returns inventory level, price trend, and market health.",
        inputSchema={
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "state": {"type": "string"},
                "property_type": {"type": "string"}
            },
            "required": ["city", "state"]
        }
    ),
    handle_get_market_saturation
)

register_tool(
    Tool(
        name="sequence_1031_exchange",
        description="Orchestrate a 1031 exchange with timeline management. Returns phases, deadlines, and replacement candidates.",
        inputSchema={
            "type": "object",
            "properties": {
                "sale_property_id": {"type": "integer"},
                "target_criteria": {"type": "object"},
                "agent_id": {"type": "integer"}
            },
            "required": ["sale_property_id", "target_criteria", "agent_id"]
        }
    ),
    handle_sequence_1031_exchange
)

register_tool(
    Tool(
        name="sequence_portfolio_acquisition",
        description="Orchestrate buying multiple properties. Returns acquisition sequence with timeline and contingencies.",
        inputSchema={
            "type": "object",
            "properties": {
                "property_ids": {"type": "array", "items": {"type": "integer"}},
                "agent_id": {"type": "integer"},
                "strategy": {"type": "string", "enum": ["parallel", "sequential"], "default": "parallel"}
            },
            "required": ["property_ids", "agent_id"]
        }
    ),
    handle_sequence_portfolio_acquisition
)

register_tool(
    Tool(
        name="sequence_sell_and_buy",
        description="Orchestrate a sale-and-buy transaction with contingencies. Returns transaction sequence with timeline.",
        inputSchema={
            "type": "object",
            "properties": {
                "sale_property_id": {"type": "integer"},
                "purchase_property_id": {"type": "integer"},
                "contingency_type": {"type": "string", "enum": ["sale_contingent", "buy_contingent"], "default": "sale_contingent"}
            },
            "required": ["sale_property_id", "purchase_property_id"]
        }
    ),
    handle_sequence_sell_and_buy
)
