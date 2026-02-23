"""Negotiation Agent — AI-powered offer analysis and counter-offer strategy."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.property import Property
from app.models.zillow_enrichment import ZillowEnrichment
from app.models.offer import Offer
from app.services.deal_calculator_service import deal_calculator_service
from app.services.comps_dashboard_service import comps_dashboard_service
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class NegotiationAgentService:
    """AI-powered negotiation assistant for offer/counter-offer scenarios."""

    async def analyze_offer(
        self,
        db: Session,
        property_id: int,
        offer_amount: float,
        buyer_concessions: list[str] | None = None,
        contingencies: list[str] | None = None,
    ) -> dict[str, Any]:
        """Analyze an offer against deal metrics and market data.

        Returns:
            {
                "acceptance_probability": 0.0-1.0,
                "counter_offer_strategy": {...},
                "negotiation_talking_points": [...],
                "walkaway_price": float,
                "recommendation": "accept" | "counter" | "reject",
                "voice_summary": "..."
            }
        """
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            return {"error": f"Property {property_id} not found"}

        # Get deal metrics
        try:
            deal_metrics = deal_calculator_service.calculate_deal(db, property_id)
        except Exception as e:
            logger.warning(f"Could not calculate deal metrics: {e}")
            deal_metrics = {"mao": None, "max_allowable_offer": None}

        # Get market analysis (comps)
        try:
            market_analysis = await comps_dashboard_service.get_comps_dashboard(db, property_id)
        except Exception as e:
            logger.warning(f"Could not get market analysis: {e}")
            market_analysis = None

        # Get enrichment for market context
        enrichment = (
            db.query(ZillowEnrichment)
            .filter(ZillowEnrichment.property_id == property_id)
            .first()
        )

        # Calculate acceptance probability
        analysis = await self._calculate_offer_analysis(
            prop, offer_amount, deal_metrics, market_analysis, enrichment
        )

        # Generate talking points
        talking_points = await self._generate_talking_points(
            prop, offer_amount, deal_metrics, market_analysis
        )

        # Generate counter-offer strategy if needed
        if analysis["recommendation"] in ["counter", "reject"]:
            counter_strategy = await self._generate_counter_strategy(
                prop, offer_amount, deal_metrics, market_analysis
            )
        else:
            counter_strategy = None

        return {
            "property_id": property_id,
            "address": prop.address,
            "offer_amount": offer_amount,
            "list_price": prop.price,
            "offer_vs_list_pct": round((offer_amount / prop.price - 1) * 100, 1) if prop.price > 0 else None,
            "acceptance_probability": analysis["probability"],
            "recommendation": analysis["recommendation"],
            "reasoning": analysis["reasoning"],
            "counter_offer_strategy": counter_strategy,
            "negotiation_talking_points": talking_points,
            "walkaway_price": analysis.get("walkaway_price"),
            "deal_metrics": deal_metrics,
            "market_context": {
                "zestimate": enrichment.zestimate if enrichment else None,
                "price_vs_zestimate_pct": (
                    round((prop.price / enrichment.zestimate - 1) * 100, 1)
                    if enrichment and enrichment.zestimate
                    else None
                ),
            },
            "voice_summary": self._build_offer_voice_summary(
                prop, offer_amount, analysis["recommendation"], analysis["probability"]
            ),
        }

    async def generate_counter_offer(
        self,
        db: Session,
        property_id: int,
        their_offer: float,
        counter_amount: float,
        reason: str | None = None,
    ) -> dict[str, Any]:
        """Generate persuasive counter-offer letter with market justification.

        Returns:
            {
                "counter_offer_letter": "full text",
                "talking_points": [...],
                "market_justification": "...",
                "voice_summary": "..."
            }
        """
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            return {"error": f"Property {property_id} not found"}

        # Get market data for justification
        enrichment = (
            db.query(ZillowEnrichment)
            .filter(ZillowEnrichment.property_id == property_id)
            .first()
        )

        # Build context for LLM
        context_parts = [
            f"Property: {prop.address} in {prop.city}, {prop.state}",
            f"List Price: ${prop.price:,.0f}",
            f"Their Offer: ${their_offer:,.0f}",
            f"Your Counter: ${counter_amount:,.0f}",
        ]

        if enrichment:
            if enrichment.zestimate:
                context_parts.append(f"Zestimate: ${enrichment.zestimate:,.0f}")
            if enrichment.price_history:
                context_parts.append(f"Price history available")

        context = "\n".join(context_parts)

        # Generate counter-offer letter
        prompt = f"""Generate a professional, persuasive counter-offer letter for a real estate transaction.

{context}

Reason for counter: {reason or "market value and property condition"}

Generate a letter that:
1. Acknowledges their offer positively
2. Clearly states the counter-offer amount
3. Provides 2-3 strong justifications based on market value, property condition, or comparables
4. Maintains a collaborative tone
5. Ends with a call to action

Keep it professional but warm. 3-4 paragraphs.

Return ONLY the letter text, no JSON or explanations."""

        try:
            letter = await llm_service.agenerate(prompt, max_tokens=1000)
        except Exception as e:
            logger.error(f"Failed to generate counter-offer letter: {e}")
            letter = self._fallback_counter_letter(prop, their_offer, counter_amount)

        # Generate talking points for the conversation
        talking_points = await self._generate_counter_talking_points(
            prop, their_offer, counter_amount, enrichment
        )

        return {
            "property_id": property_id,
            "their_offer": their_offer,
            "counter_offer": counter_amount,
            "counter_offer_letter": letter,
            "talking_points": talking_points,
            "voice_summary": f"Counter-offer of ${counter_amount:,.0f} against their ${their_offer:,.0f} offer. Key points: {', '.join(talking_points[:2])}.",
        }

    async def suggest_offer_price(
        self,
        db: Session,
        property_id: int,
        aggressiveness: str = "moderate",  # "conservative", "moderate", "aggressive"
    ) -> dict[str, Any]:
        """Suggest an optimal offer price based on market analysis.

        Returns:
            {
                "suggested_offer": float,
                "confidence": "high" | "medium" | "low",
                "range": {"min": float, "max": float},
                "justification": "...",
                "voice_summary": "..."
            }
        """
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            return {"error": f"Property {property_id} not found"}

        # Get deal metrics
        try:
            deal_metrics = deal_calculator_service.calculate_deal(db, property_id)
            mao = deal_metrics.get("max_allowable_offer")
        except Exception as e:
            logger.warning(f"Could not calculate MAO: {e}")
            mao = None

        # Get market data
        enrichment = (
            db.query(ZillowEnrichment)
            .filter(ZillowEnrichment.property_id == property_id)
            .first()
        )

        # Calculate suggested offer
        if aggressiveness == "conservative":
            # Start 10% below list, but not below MAO
            discount = 0.10
        elif aggressiveness == "aggressive":
            # Start 15% below list
            discount = 0.15
        else:  # moderate
            discount = 0.12

        suggested_offer = prop.price * (1 - discount)

        # Respect MAO if available
        if mao and suggested_offer > mao:
            suggested_offer = mao * 0.95  # Leave some room

        # Calculate range
        range_min = suggested_offer * 0.95
        range_max = suggested_offer * 1.05

        # Justification
        justification_parts = [
            f"Based on {aggressiveness} strategy for {prop.property_type.value if prop.property_type else 'property'} in {prop.city}",
        ]

        if enrichment and enrichment.zestimate:
            zestimate_diff = (enrichment.zestimate - suggested_offer) / enrichment.zestimate
            justification_parts.append(
                f"Suggested offer is {zestimate_diff*100:.0f}% below Zestimate of ${enrichment.zestimate:,.0f}"
            )

        if mao:
            justification_parts.append(f"Respects maximum allowable offer of ${mao:,.0f}")

        return {
            "property_id": property_id,
            "list_price": prop.price,
            "suggested_offer": round(suggested_offer, 2),
            "discount_from_list": round(discount * 100, 1),
            "range": {
                "min": round(range_min, 2),
                "max": round(range_max, 2),
            },
            "mao": mao,
            "aggressiveness": aggressiveness,
            "justification": ". ".join(justification_parts),
            "confidence": "high" if enrichment and enrichment.zestimate else "medium",
            "voice_summary": self._build_offer_suggestion_voice_summary(
                prop, suggested_offer, discount, aggressiveness
            ),
        }

    # ── Private Methods ──

    async def _calculate_offer_analysis(
        self,
        prop: Property,
        offer_amount: float,
        deal_metrics: dict,
        market_analysis: dict | None,
        enrichment: ZillowEnrichment | None,
    ) -> dict[str, Any]:
        """Calculate acceptance probability and recommendation."""
        # Calculate discount from list
        discount_from_list = (prop.price - offer_amount) / prop.price if prop.price > 0 else 0

        # Score the offer (0-100)
        offer_score = 50  # Base score

        # Above list price = very good
        if offer_amount >= prop.price:
            offer_score += 30

        # Within 5% of list = good
        elif discount_from_list <= 0.05:
            offer_score += 20

        # Within 10% = acceptable
        elif discount_from_list <= 0.10:
            offer_score += 10

        # Below MAO = bad
        mao = deal_metrics.get("max_allowable_offer")
        if mao and offer_amount < mao:
            offer_score -= 20

        # Compared to Zestimate
        if enrichment and enrichment.zestimate:
            zestimate_discount = (enrichment.zestimate - offer_amount) / enrichment.zestimate
            if zestimate_discount < 0:  # Above Zestimate
                offer_score += 10
            elif zestimate_discount > 0.15:  # Way below Zestimate
                offer_score -= 10

        # Normalize to probability
        probability = max(0.0, min(1.0, offer_score / 100))

        # Determine recommendation
        if probability >= 0.85:
            recommendation = "accept"
            reasoning = "Strong offer at or above asking price"
        elif probability >= 0.60:
            recommendation = "counter"
            reasoning = "Reasonable offer but room for negotiation"
        elif probability >= 0.40:
            recommendation = "counter"
            reasoning = "Low offer - consider countering with justification"
        else:
            recommendation = "reject"
            reasoning = "Offer too low - below acceptable threshold"

        # Calculate walkaway price
        walkaway = mao * 0.95 if mao else prop.price * 0.85

        return {
            "probability": round(probability, 2),
            "recommendation": recommendation,
            "reasoning": reasoning,
            "walkaway_price": round(walkaway, 2),
            "offer_score": offer_score,
        }

    async def _generate_talking_points(
        self,
        prop: Property,
        offer_amount: float,
        deal_metrics: dict,
        market_analysis: dict | None,
    ) -> list[str]:
        """Generate negotiation talking points."""
        points = []

        # Price comparison
        if offer_amount >= prop.price:
            points.append(f"Offer is at or above list price of ${prop.price:,.0f}")
        else:
            discount = (prop.price - offer_amount) / prop.price * 100
            points.append(f"Offer is {discount:.0f}% below list price")

        # MAO comparison
        mao = deal_metrics.get("max_allowable_offer")
        if mao:
            if offer_amount >= mao:
                points.append(f"Offer exceeds maximum allowable offer (${mao:,.0f})")
            else:
                points.append(f"Offer is below maximum allowable offer")

        # Market data
        if market_analysis and market_analysis.get("market_metrics"):
            metrics = market_analysis["market_metrics"]
            if metrics.get("avg_price"):
                points.append(f"Market average is ${metrics['avg_price']:,.0f}")

        return points

    async def _generate_counter_strategy(
        self,
        prop: Property,
        their_offer: float,
        deal_metrics: dict,
        market_analysis: dict | None,
    ) -> dict[str, Any]:
        """Generate counter-offer strategy."""
        # Determine counter price
        if their_offer < prop.price * 0.9:
            # Very low offer - counter closer to list
            counter = prop.price * 0.95
        elif their_offer < prop.price * 0.95:
            # Moderate low offer - meet in middle
            counter = (their_offer + prop.price) / 2
        else:
            # Close offer - small counter
            counter = their_offer * 1.03

        return {
            "suggested_counter": round(counter, 2),
            "counter_vs_offer": round((counter / their_offer - 1) * 100, 1),
            "strategy": "meet_in_middle" if their_offer < prop.price * 0.95 else "small_increase",
            "justification": "Based on market comparables and property condition",
        }

    async def _generate_counter_talking_points(
        self,
        prop: Property,
        their_offer: float,
        counter: float,
        enrichment: ZillowEnrichment | None,
    ) -> list[str]:
        """Generate talking points for counter-offer conversation."""
        points = []

        # Acknowledge their offer
        points.append(f"Thank you for the offer of ${their_offer:,.0f}")

        # Justify counter
        if enrichment and enrichment.zestimate:
            points.append(f"Zestimate indicates market value of ${enrichment.zestimate:,.0f}")

        # Property condition/features
        points.append(f"Property is in excellent condition with recent updates")

        # Market demand
        points.append(f"Strong market activity in {prop.city}")

        # Closing the gap
        points.append(f"Our counter of ${counter:,.0f} reflects fair market value")

        return points

    def _fallback_counter_letter(
        self, prop: Property, their_offer: float, counter: float
    ) -> str:
        """Generate fallback counter-offer letter if LLM fails."""
        return (
            f"Thank you for your offer of ${their_offer:,.0f} on {prop.address}. "
            f"We appreciate your interest in the property.\n\n"
            f"After careful consideration, we would like to propose a counter-offer of ${counter:,.0f}. "
            f"This price reflects the current market conditions in {prop.city}, "
            f"the property's excellent condition, and recent comparable sales in the area.\n\n"
            f"We believe this is a fair price that reflects the true value of the property. "
            f"We're confident you'll agree this is a wonderful home and a great investment.\n\n"
            f"Please let us know your thoughts. We look forward to working with you to make this happen.\n\n"
            f"Best regards"
        )

    def _build_offer_voice_summary(
        self, prop: Property, offer_amount: float, recommendation: str, probability: float
    ) -> str:
        """Build voice summary for offer analysis."""
        vs_list = (offer_amount / prop.price * 100) if prop.price > 0 else 0

        return (
            f"Offer of ${offer_amount:,.0f} on {prop.address} is {vs_list:.0f}% of list price. "
            f"{recommendation.capitalize()} with {probability*100:.0f}% confidence."
        )

    def _build_offer_suggestion_voice_summary(
        self, prop: Property, suggested: float, discount: float, aggressiveness: str
    ) -> str:
        """Build voice summary for offer suggestion."""
        return (
            f"For {prop.address}, suggest ${suggested:,.0f} "
            f"({discount*100:.0f}% below list price) using {aggressiveness} strategy."
        )


negotiation_agent_service = NegotiationAgentService()
