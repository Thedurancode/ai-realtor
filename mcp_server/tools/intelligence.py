"""Intelligence tools module - registers all intelligence MCP tools."""

from mcp_server.server import register_tool

# Import all intelligence tools (they register themselves via @mcp.tool() decorators)
# We need to manually convert them to our register_tool format

from typing import Any, Optional
from datetime import datetime

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


# ── Helper Functions ──

def _get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Register Intelligence Tools ──

@register_tool({
    "name": "predict_property_outcome",
    "description": "Predict closing probability and recommend actions for a property. Returns closing probability (0-100%), confidence, risk factors, strengths, and recommended actions.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "property_id": {"type": "integer", "description": "Property to analyze"}
        },
        "required": ["property_id"]
    }
})
def predict_property_outcome(property_id: int) -> str:
    db = SessionLocal()
    try:
        result = predictive_intelligence_service.predict_property_outcome(db, property_id)
        if "error" in result:
            return f"Error: {result['error']}"
        return result.get("voice_summary", f"Closing Probability: {result['closing_probability']*100:.0f}%")
    finally:
        db.close()


@register_tool({
    "name": "recommend_next_action",
    "description": "Get AI-recommended next action for a property with reasoning. Returns recommended action, reasoning, priority, and expected impact.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "property_id": {"type": "integer"},
            "context": {"type": "string", "description": "Optional context (e.g., offer_received, inspection_complete)"}
        },
        "required": ["property_id"]
    }
})
def recommend_next_action(property_id: int, context: Optional[str] = None) -> str:
    db = SessionLocal()
    try:
        result = predictive_intelligence_service.recommend_next_action(db, property_id, context)
        if "error" in result:
            return f"Error: {result['error']}"
        return result.get("voice_summary", f"Action: {result['recommended_action']}, Priority: {result['priority']}")
    finally:
        db.close()


@register_tool({
    "name": "batch_predict_outcomes",
    "description": "Predict outcomes for multiple properties, sorted by priority (lowest probability first)",
    "inputSchema": {
        "type": "object",
        "properties": {
            "property_ids": {"type": "array", "items": {"type": "integer"}, "description": "Optional list of property IDs"}
        }
    }
})
def batch_predict_outcomes(property_ids: Optional[list[int]] = None) -> str:
    db = SessionLocal()
    try:
        result = predictive_intelligence_service.batch_predict_outcomes(db, property_ids)
        return result.get("voice_summary", f"Analyzed {result.get('total_analyzed', 0)} properties")
    finally:
        db.close()


@register_tool({
    "name": "record_deal_outcome",
    "description": "Record actual deal outcome for machine learning. Status: closed_won, closed_lost, withdrawn, or stalled",
    "inputSchema": {
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
})
def record_deal_outcome(property_id: int, status: str, final_sale_price: Optional[float] = None, outcome_reason: Optional[str] = None, lessons_learned: Optional[str] = None) -> str:
    db = SessionLocal()
    try:
        outcome_status = OutcomeStatus(status)
        result = learning_system_service.record_outcome(db, property_id, outcome_status, final_sale_price, outcome_reason, lessons_learned)
        if "error" in result:
            return f"Error: {result['error']}"
        return f"Recorded {status} outcome for property {property_id}. Learning system updated."
    finally:
        db.close()


@register_tool({
    "name": "get_agent_success_patterns",
    "description": "Get agent's success patterns from historical performance. Returns best property types, cities, price ranges, and success factors.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "agent_id": {"type": "integer"},
            "period": {"type": "string", "enum": ["week", "month", "quarter", "year"], "default": "month"}
        },
        "required": ["agent_id"]
    }
})
def get_agent_success_patterns(agent_id: int, period: str = "month") -> str:
    db = SessionLocal()
    try:
        result = learning_system_service.get_agent_success_patterns(db, agent_id, period)
        return result.get("voice_summary", f"Analyzed patterns for agent {agent_id}")
    finally:
        db.close()


@register_tool({
    "name": "scan_market_opportunities",
    "description": "Scan for opportunities matching agent's success patterns. Returns top opportunities with match reasons and ROI estimates.",
    "inputSchema": {
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
})
def scan_market_opportunities(agent_id: int, limit: int = 10, min_score: float = 70, property_types: Optional[list[str]] = None, cities: Optional[list[str]] = None, max_price: Optional[float] = None) -> str:
    db = SessionLocal()
    try:
        result = market_opportunity_scanner.scan_market_opportunities(db, agent_id, limit, min_score, property_types, cities, max_price)
        return result.get("voice_summary", f"Found {result.get('opportunities_found', 0)} opportunities")
    finally:
        db.close()


@register_tool({
    "name": "detect_market_shifts",
    "description": "Detect significant changes in market conditions (price drops/surges >10%)",
    "inputSchema": {
        "type": "object",
        "properties": {
            "agent_id": {"type": "integer"},
            "cities": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["agent_id"]
    }
})
def detect_market_shifts(agent_id: int, cities: Optional[list[str]] = None) -> str:
    db = SessionLocal()
    try:
        result = market_opportunity_scanner.detect_market_shifts(db, agent_id, cities)
        return result.get("voice_summary", f"Detected {result.get('shifts_detected', 0)} market shifts")
    finally:
        db.close()


@register_tool({
    "name": "find_similar_properties",
    "description": "Find similar properties for comparison. Returns similar properties with similarity scores.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "property_id": {"type": "integer"},
            "agent_id": {"type": "integer"},
            "limit": {"type": "integer", "default": 5}
        },
        "required": ["property_id"]
    }
})
def find_similar_properties(property_id: int, agent_id: Optional[int] = None, limit: int = 5) -> str:
    db = SessionLocal()
    try:
        result = market_opportunity_scanner.find_similar_deals(db, property_id, agent_id, limit)
        similar_count = len(result.get("similar_properties", []))
        return result.get("voice_summary", f"Found {similar_count} similar properties")
    finally:
        db.close()


@register_tool({
    "name": "score_relationship_health",
    "description": "Get relationship health score for a contact (0-100). Returns health score, trend, and recommendations.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "contact_id": {"type": "integer"}
        },
        "required": ["contact_id"]
    }
})
def score_relationship_health(contact_id: int) -> str:
    db = SessionLocal()
    try:
        result = relationship_intelligence_service.score_relationship_health(db, contact_id)
        if "error" in result:
            return f"Error: {result['error']}"
        return result.get("voice_summary", f"Relationship health: {result['health_score']:.0f}/100")
    finally:
        db.close()


@register_tool({
    "name": "predict_best_contact_method",
    "description": "Predict the best contact method: phone, email, or text. Returns recommendation with reasoning.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "contact_id": {"type": "integer"},
            "message_type": {"type": "string", "default": "check_in"}
        },
        "required": ["contact_id"]
    }
})
def predict_best_contact_method(contact_id: int, message_type: str = "check_in") -> str:
    db = SessionLocal()
    try:
        result = relationship_intelligence_service.predict_best_contact_method(db, contact_id, message_type)
        if "error" in result:
            return f"Error: {result['error']}"
        return result.get("voice_summary", f"Recommend {result['recommended_method']}")
    finally:
        db.close()


@register_tool({
    "name": "analyze_offer",
    "description": "Analyze an offer against deal metrics and market data. Returns acceptance probability, counter strategy, and walkaway price.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "property_id": {"type": "integer"},
            "offer_amount": {"type": "number"},
            "buyer_concessions": {"type": "array", "items": {"type": "string"}},
            "contingencies": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["property_id", "offer_amount"]
    }
})
def analyze_offer(property_id: int, offer_amount: float, buyer_concessions: Optional[list[str]] = None, contingencies: Optional[list[str]] = None) -> str:
    db = SessionLocal()
    try:
        result = negotiation_agent_service.analyze_offer(db, property_id, offer_amount, buyer_concessions, contingencies)
        if "error" in result:
            return f"Error: {result['error']}"
        return f"{result['voice_summary']} Recommendation: {result['recommendation']}, Walkaway: ${result.get('walkaway_price', 0):,.0f}"
    finally:
        db.close()


@register_tool({
    "name": "generate_counter_offer",
    "description": "Generate persuasive counter-offer letter with market justification",
    "inputSchema": {
        "type": "object",
        "properties": {
            "property_id": {"type": "integer"},
            "their_offer": {"type": "number"},
            "counter_amount": {"type": "number"},
            "reason": {"type": "string"}
        },
        "required": ["property_id", "their_offer", "counter_amount"]
    }
})
def generate_counter_offer(property_id: int, their_offer: float, counter_amount: float, reason: Optional[str] = None) -> str:
    db = SessionLocal()
    try:
        result = negotiation_agent_service.generate_counter_offer(db, property_id, their_offer, counter_amount, reason)
        if "error" in result:
            return f"Error: {result['error']}"
        return f"{result['voice_summary']}\n\n{result['counter_offer_letter']}"
    finally:
        db.close()


@register_tool({
    "name": "suggest_offer_price",
    "description": "Suggest an optimal offer price based on market analysis (conservative/moderate/aggressive)",
    "inputSchema": {
        "type": "object",
        "properties": {
            "property_id": {"type": "integer"},
            "aggressiveness": {"type": "string", "enum": ["conservative", "moderate", "aggressive"], "default": "moderate"}
        },
        "required": ["property_id"]
    }
})
def suggest_offer_price(property_id: int, aggressiveness: str = "moderate") -> str:
    db = SessionLocal()
    try:
        result = negotiation_agent_service.suggest_offer_price(db, property_id, aggressiveness)
        if "error" in result:
            return f"Error: {result['error']}"
        return f"{result['voice_summary']} Suggested: ${result['suggested_offer']:,.0f}"
    finally:
        db.close()


@register_tool({
    "name": "analyze_inspection_report",
    "description": "Extract key issues from inspection report using NLP. Returns critical issues, repair estimates, and deal killers.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "property_id": {"type": "integer"},
            "document_text": {"type": "string"}
        },
        "required": ["property_id", "document_text"]
    }
})
def analyze_inspection_report(property_id: int, document_text: str) -> str:
    db = SessionLocal()
    try:
        result = document_analyzer_service.analyze_inspection_report(db, property_id, document_text, create_note=True)
        if "error" in result:
            return f"Error: {result['error']}"
        return f"{result['voice_summary']} Critical Issues: {len(result['critical_issues'])}, Repairs: ${result['total_repair_estimate']:,.0f}"
    finally:
        db.close()


@register_tool({
    "name": "extract_contract_terms",
    "description": "Extract key terms from a contract document. Returns parties, dates, financial terms, and contingencies.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "property_id": {"type": "integer"},
            "contract_text": {"type": "string"}
        },
        "required": ["property_id", "contract_text"]
    }
})
def extract_contract_terms(property_id: int, contract_text: str) -> str:
    db = SessionLocal()
    try:
        result = document_analyzer_service.extract_contract_terms(db, property_id, contract_text)
        if "error" in result:
            return f"Error: {result['error']}"
        return result.get("voice_summary", "Contract terms extracted successfully")
    finally:
        db.close()


@register_tool({
    "name": "analyze_market_competition",
    "description": "Analyze competing agents in a specific market. Returns most active agents, fastest closers, and winning bid patterns.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "city": {"type": "string"},
            "state": {"type": "string"},
            "property_type": {"type": "string"}
        },
        "required": ["city", "state"]
    }
})
def analyze_market_competition(city: str, state: str, property_type: Optional[str] = None) -> str:
    db = SessionLocal()
    try:
        result = competitive_intelligence_service.analyze_market_competition(db, city, state, property_type)
        return result.get("voice_summary", f"Analyzed competition in {city}, {state}")
    finally:
        db.close()


@register_tool({
    "name": "detect_competitive_activity",
    "description": "Alert if competition is interested in the same property. Returns activity alerts with urgency.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "property_id": {"type": "integer"}
        },
        "required": ["property_id"]
    }
})
def detect_competitive_activity(property_id: int) -> str:
    db = SessionLocal()
    try:
        result = competitive_intelligence_service.detect_competitive_activity(db, property_id)
        if "error" in result:
            return f"Error: {result['error']}"
        return result.get("voice_summary", "No competitive activity detected")
    finally:
        db.close()


@register_tool({
    "name": "get_market_saturation",
    "description": "Analyze market saturation - inventory levels and demand. Returns inventory level, price trend, and market health.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "city": {"type": "string"},
            "state": {"type": "string"},
            "property_type": {"type": "string"}
        },
        "required": ["city", "state"]
    }
})
def get_market_saturation(city: str, state: str, property_type: Optional[str] = None) -> str:
    db = SessionLocal()
    try:
        result = competitive_intelligence_service.get_market_saturation(db, city, state, property_type)
        return result.get("voice_summary", f"Market: {result['inventory_level']} inventory, {result['price_trend']} prices")
    finally:
        db.close()


@register_tool({
    "name": "sequence_1031_exchange",
    "description": "Orchestrate a 1031 exchange with timeline management. Returns phases, deadlines, and replacement candidates.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "sale_property_id": {"type": "integer"},
            "target_criteria": {"type": "object"},
            "agent_id": {"type": "integer"}
        },
        "required": ["sale_property_id", "target_criteria", "agent_id"]
    }
})
def sequence_1031_exchange(sale_property_id: int, target_criteria: dict, agent_id: int) -> str:
    db = SessionLocal()
    try:
        result = deal_sequencer_service.sequence_1031_exchange(db, sale_property_id, target_criteria, agent_id)
        if "error" in result:
            return f"Error: {result['error']}"
        return result.get("voice_summary", "1031 exchange sequenced with automated reminders")
    finally:
        db.close()


@register_tool({
    "name": "sequence_portfolio_acquisition",
    "description": "Orchestrate buying multiple properties. Returns acquisition sequence with timeline and contingencies.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "property_ids": {"type": "array", "items": {"type": "integer"}},
            "agent_id": {"type": "integer"},
            "strategy": {"type": "string", "enum": ["parallel", "sequential"], "default": "parallel"}
        },
        "required": ["property_ids", "agent_id"]
    }
})
def sequence_portfolio_acquisition(property_ids: list[int], agent_id: int, strategy: str = "parallel") -> str:
    db = SessionLocal()
    try:
        result = deal_sequencer_service.sequence_portfolio_acquisition(db, property_ids, agent_id, strategy)
        if "error" in result:
            return f"Error: {result['error']}"
        return f"{result['voice_summary']} Total: ${result['total_investment']:,.0f}, Timeline: {result['estimated_timeline_days']} days"
    finally:
        db.close()


@register_tool({
    "name": "sequence_sell_and_buy",
    "description": "Orchestrate a sale-and-buy transaction with contingencies. Returns transaction sequence with timeline.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "sale_property_id": {"type": "integer"},
            "purchase_property_id": {"type": "integer"},
            "contingency_type": {"type": "string", "enum": ["sale_contingent", "buy_contingent"], "default": "sale_contingent"}
        },
        "required": ["sale_property_id", "purchase_property_id"]
    }
})
def sequence_sell_and_buy(sale_property_id: int, purchase_property_id: int, contingency_type: str = "sale_contingent") -> str:
    db = SessionLocal()
    try:
        result = deal_sequencer_service.sequence_sell_and_buy(db, sale_property_id, purchase_property_id, contingency_type)
        if "error" in result:
            return f"Error: {result['error']}"
        return result.get("voice_summary", "Sell-and-buy transaction sequenced")
    finally:
        db.close()
