"""Intelligence API endpoints —谈判 agents, campaigns, documents, and competitive analysis."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.services.autonomous_campaign_manager import autonomous_campaign_manager
from app.services.negotiation_agent_service import negotiation_agent_service
from app.services.document_analyzer_service import document_analyzer_service
from app.services.competitive_intelligence_service import competitive_intelligence_service
from app.services.deal_sequencer_service import deal_sequencer_service

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


# ── Autonomous Campaign Manager ──


@router.post("/campaigns/{campaign_id}/optimize")
async def optimize_campaign_parameters(campaign_id: int, db: Session = Depends(get_db)):
    """Auto-adjust call time, message, targeting based on performance."""
    result = await autonomous_campaign_manager.optimize_campaign_parameters(db, campaign_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/campaigns/autonomous")
async def run_autonomous_campaign(
    goal: str,
    agent_id: int,
    campaign_name: Optional[str] = None,
    max_duration_hours: int = 24,
    db: Session = Depends(get_db),
):
    """End-to-end autonomous campaign: plan → execute → optimize → report.

    This creates and runs a campaign based on a natural language goal,
    optimizing automatically based on responses.
    """
    result = await autonomous_campaign_manager.autonomous_campaign_execution(
        db, goal, agent_id, campaign_name, max_duration_hours
    )
    return result


@router.get("/campaigns/{campaign_id}/roi")
async def get_campaign_roi(campaign_id: int, db: Session = Depends(get_db)):
    """Calculate ROI of a campaign (cost vs outcomes)."""
    result = await autonomous_campaign_manager.get_campaign_roi(db, campaign_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ── Negotiation Agent ──


class AnalyzeOfferRequest(BaseModel):
    offer_amount: float
    buyer_concessions: Optional[List[str]] = None
    contingencies: Optional[List[str]] = None


@router.post("/negotiation/property/{property_id}/analyze-offer")
async def analyze_offer(
    property_id: int,
    request: AnalyzeOfferRequest,
    db: Session = Depends(get_db),
):
    """Analyze an offer against deal metrics and market data.

    Returns acceptance probability, counter-offer strategy,
    negotiation talking points, and walkaway price.
    """
    result = await negotiation_agent_service.analyze_offer(
        db,
        property_id,
        request.offer_amount,
        request.buyer_concessions,
        request.contingencies,
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/negotiation/property/{property_id}/counter-offer")
async def generate_counter_offer(
    property_id: int,
    their_offer: float,
    counter_amount: float,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Generate persuasive counter-offer letter with market justification."""
    result = await negotiation_agent_service.generate_counter_offer(
        db, property_id, their_offer, counter_amount, reason
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/negotiation/property/{property_id}/suggest-price")
async def suggest_offer_price(
    property_id: int,
    aggressiveness: str = "moderate",  # conservative, moderate, aggressive
    db: Session = Depends(get_db),
):
    """Suggest an optimal offer price based on market analysis."""
    result = await negotiation_agent_service.suggest_offer_price(
        db, property_id, aggressiveness
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ── Document Analysis ──


@router.post("/documents/inspection")
async def analyze_inspection_report(
    property_id: int,
    document_text: str,
    create_note: bool = True,
    db: Session = Depends(get_db),
):
    """Extract key issues from inspection report using NLP.

    Returns critical issues, repair estimates, negotiation leverage,
    and deal killers.
    """
    result = await document_analyzer_service.analyze_inspection_report(
        db, property_id, document_text, create_note
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/documents/appraisals/compare")
async def compare_appraisals(
    property_id: int,
    appraisal_docs: List[dict],  # [{"text": str, "source": str, "date": str}]
    db: Session = Depends(get_db),
):
    """Compare multiple appraisals and flag discrepancies.

    Returns discrepancies in values, measurements, and recommendations.
    """
    result = await document_analyzer_service.compare_appraisals(
        db, property_id, appraisal_docs
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/documents/contract/extract")
async def extract_contract_terms(
    property_id: int,
    contract_text: str,
    db: Session = Depends(get_db),
):
    """Extract key terms from a contract document.

    Returns parties, dates, financial terms, contingencies, and obligations.
    """
    result = await document_analyzer_service.extract_contract_terms(
        db, property_id, contract_text
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ── Competitive Intelligence ──


@router.get("/competition/market/{city}/{state}")
async def analyze_market_competition(
    city: str,
    state: str,
    property_type: Optional[str] = None,
    days_back: int = 90,
    db: Session = Depends(get_db),
):
    """Analyze competing agents in a specific market.

    Returns most active agents, fastest closers, highest spenders,
    and winning bid patterns.
    """
    result = await competitive_intelligence_service.analyze_market_competition(
        db, city, state, property_type, days_back
    )
    return result


@router.get("/competition/property/{property_id}/activity")
async def detect_competitive_activity(property_id: int, db: Session = Depends(get_db)):
    """Alert if competition is interested in the same property.

    Monitors viewing activity, multiple offers, and price acceleration.
    """
    result = await competitive_intelligence_service.detect_competitive_activity(
        db, property_id
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/competition/market/{city}/{state}/saturation")
async def get_market_saturation(
    city: str,
    state: str,
    property_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Analyze market saturation - inventory levels and demand.

    Returns inventory level, days on market, price trend, and market health.
    """
    result = await competitive_intelligence_service.get_market_saturation(
        db, city, state, property_type
    )
    return result


# ── Deal Sequencer ──


class Sequence1031Request(BaseModel):
    sale_property_id: int
    target_criteria: dict
    agent_id: int


@router.post("/sequencing/1031-exchange")
async def sequence_1031_exchange(
    request: Sequence1031Request,
    db: Session = Depends(get_db),
):
    """Orchestrate a 1031 exchange with timeline management.

    Identifies replacement properties, manages 45/180 day deadlines,
    and creates automated reminders.
    """
    result = await deal_sequencer_service.sequence_1031_exchange(
        db,
        request.sale_property_id,
        request.target_criteria,
        request.agent_id,
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/sequencing/portfolio-acquisition")
async def sequence_portfolio_acquisition(
    property_ids: List[int],
    agent_id: int,
    strategy: str = "parallel",  # parallel or sequential
    db: Session = Depends(get_db),
):
    """Orchestrate buying multiple properties with optimal ordering.

    Prioritizes by deal score, identifies contingencies,
    and finds parallelizable actions.
    """
    result = await deal_sequencer_service.sequence_portfolio_acquisition(
        db, property_ids, agent_id, strategy
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/sequencing/sell-and-buy")
async def sequence_sell_and_buy(
    sale_property_id: int,
    purchase_property_id: int,
    contingency_type: str = "sale_contingent",  # sale_contingent or buy_contingent
    db: Session = Depends(get_db),
):
    """Orchestrate a sale-and-buy transaction with contingencies.

    Manages the dependency between sale and purchase closings.
    """
    result = await deal_sequencer_service.sequence_sell_and_buy(
        db, sale_property_id, purchase_property_id, contingency_type
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
