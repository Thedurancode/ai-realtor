"""Predictive Intelligence Engine — AI-powered outcome predictions and recommendations."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.property import Property, PropertyStatus
from app.models.zillow_enrichment import ZillowEnrichment
from app.models.contract import Contract, ContractStatus
from app.models.contact import Contact
from app.models.skip_trace import SkipTrace
from app.models.conversation_history import ConversationHistory
from app.models.property_note import PropertyNote
from app.models.offer import Offer, OfferStatus
from app.services.property_scoring_service import property_scoring_service
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class PredictiveIntelligenceService:
    """Predictive analytics for deal outcomes and optimal actions."""

    async def predict_property_outcome(
        self, db: Session, property_id: int
    ) -> dict[str, Any]:
        """Predict likelihood of deal closing with confidence %.

        Returns:
            {
                "closing_probability": 0.0-1.0,
                "confidence": "high" | "medium" | "low",
                "time_to_close_estimate": days,
                "risk_factors": [...],
                "strengths": [...],
                "recommended_actions": [...]
            }
        """
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            return {"error": f"Property {property_id} not found"}

        signals = await self._collect_prediction_signals(db, prop)
        prediction = self._calculate_closing_probability(signals)

        # Generate recommended actions based on weak signals
        recommendations = self._generate_recommendations(prop, signals, prediction)

        # Build voice summary
        voice_summary = self._build_prediction_voice_summary(
            prop, prediction, recommendations
        )

        return {
            "property_id": prop.id,
            "address": prop.address,
            "closing_probability": prediction["probability"],
            "confidence": prediction["confidence"],
            "time_to_close_estimate_days": prediction["estimated_days"],
            "risk_factors": prediction["risk_factors"],
            "strengths": prediction["strengths"],
            "recommended_actions": recommendations,
            "signal_breakdown": signals,
            "voice_summary": voice_summary,
        }

    async def recommend_next_action(
        self, db: Session, property_id: int, context: str | None = None
    ) -> dict[str, Any]:
        """AI-recommended next action with reasoning.

        Args:
            property_id: Property to analyze
            context: Optional context (e.g., "offer_received", "inspection_complete")

        Returns:
            {
                "action": "enrich_property" | "skip_trace" | "attach_contracts" | ...,
                "reason": "Why this action is recommended",
                "priority": "high" | "medium" | "low",
                "expected_impact": "How this will improve outcomes",
                "voice_summary": "Natural language explanation"
            }
        """
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            return {"error": f"Property {property_id} not found"}

        # Collect current state
        state = await self._assess_property_state(db, prop)

        # Get prediction to inform action
        prediction = await self.predict_property_outcome(db, prop.id)

        # Use LLM to reason about best next action
        action_recommendation = await self._llm_recommend_action(
            prop, state, prediction, context
        )

        return {
            "property_id": prop.id,
            "address": prop.address,
            "current_state": state,
            "recommended_action": action_recommendation["action"],
            "reasoning": action_recommendation["reasoning"],
            "priority": action_recommendation["priority"],
            "expected_impact": action_recommendation["expected_impact"],
            "closing_probability_change": action_recommendation.get(
                "probability_improvement"
            ),
            "voice_summary": action_recommendation["voice_summary"],
        }

    async def batch_predict_outcomes(
        self, db: Session, property_ids: list[int] | None = None
    ) -> dict[str, Any]:
        """Predict outcomes for multiple properties.

        Returns prioritized list: highest priority = lowest closing probability.
        """
        query = db.query(Property)

        if property_ids:
            query = query.filter(Property.id.in_(property_ids))

        # Filter out completed deals
        query = query.filter(Property.status != PropertyStatus.COMPLETE)

        properties = query.limit(50).all()

        results = []
        for prop in properties:
            try:
                prediction = await self.predict_property_outcome(db, prop.id)
                results.append(prediction)
            except Exception as e:
                logger.error(f"Error predicting outcome for property {prop.id}: {e}")
                results.append({"property_id": prop.id, "error": str(e)})

        # Sort by closing probability (lowest first = highest priority)
        sorted_results = sorted(
            [r for r in results if "closing_probability" in r],
            key=lambda x: x["closing_probability"],
        )

        # Generate summary
        high_risk = [r for r in sorted_results if r["closing_probability"] < 0.4]
        medium_risk = [
            r for r in sorted_results if 0.4 <= r["closing_probability"] < 0.7
        ]
        low_risk = [r for r in sorted_results if r["closing_probability"] >= 0.7]

        voice = (
            f"Analyzed {len(sorted_results)} properties. "
            f"{len(high_risk)} high-risk, {len(medium_risk)} medium-risk, {len(low_risk)} low-risk. "
            f"Focus on {len(high_risk)} high-risk properties first."
        )

        return {
            "total_analyzed": len(sorted_results),
            "high_risk_count": len(high_risk),
            "medium_risk_count": len(medium_risk),
            "low_risk_count": len(low_risk),
            "predictions": sorted_results,
            "high_priority_properties": high_risk[:5],  # Top 5 to focus on
            "voice_summary": voice,
        }

    # ── Private Methods ──

    async def _collect_prediction_signals(
        self, db: Session, prop: Property
    ) -> dict[str, Any]:
        """Collect all predictive signals for a property."""
        signals = {
            "property": {},
            "deal_score": {},
            "enrichment": {},
            "contracts": {},
            "contacts": {},
            "skip_trace": {},
            "activity": {},
            "offers": {},
        }

        # Basic property info
        signals["property"] = {
            "status": prop.status.value if prop.status else None,
            "deal_type": prop.deal_type.value if prop.deal_type else None,
            "property_type": prop.property_type.value if prop.property_type else None,
            "price": prop.price,
            "days_since_creation": (
                datetime.now(timezone.utc) - prop.created_at
            ).days
            if prop.created_at
            else None,
        }

        # Deal score (strongest signal)
        if prop.deal_score is not None:
            signals["deal_score"] = {
                "score": prop.deal_score,
                "grade": prop.score_grade,
                "has_breakdown": prop.score_breakdown is not None,
            }

        # Zillow enrichment
        enrichment = (
            db.query(ZillowEnrichment)
            .filter(ZillowEnrichment.property_id == prop.id)
            .first()
        )
        if enrichment:
            signals["enrichment"] = {
                "has_zestimate": enrichment.zestimate is not None,
                "zestimate_spread_pct": (
                    ((enrichment.zestimate - prop.price) / prop.price * 100)
                    if enrichment.zestimate and prop.price
                    else None
                ),
                "has_photos": bool(enrichment.photos and len(enrichment.photos) > 0),
                "days_on_zillow": enrichment.days_on_zillow,
                "has_schools": bool(enrichment.schools),
            }

        # Contracts
        contracts = (
            db.query(Contract).filter(Contract.property_id == prop.id).all()
        )
        required_contracts = [c for c in contracts if c.is_required]
        completed_contracts = [
            c for c in contracts if c.status == ContractStatus.COMPLETED
        ]

        signals["contracts"] = {
            "total_contracts": len(contracts),
            "required_total": len(required_contracts),
            "required_completed": len(
                [c for c in required_contracts if c.status == ContractStatus.COMPLETED]
            ),
            "completion_rate": (
                len(completed_contracts) / len(contracts) * 100 if contracts else 0
            ),
            "has_unsigned_required": any(
                c.status != ContractStatus.COMPLETED for c in required_contracts
            ),
        }

        # Contacts
        contacts = db.query(Contact).filter(Contact.property_id == prop.id).all()
        key_roles = {"buyer", "seller", "lawyer", "attorney", "lender"}
        signals["contacts"] = {
            "total_contacts": len(contacts),
            "has_key_roles": any(
                c.role and c.role.value in key_roles for c in contacts
            ),
            "has_buyer": any(c.role and c.role.value == "buyer" for c in contacts),
            "has_seller": any(c.role and c.role.value == "seller" for c in contacts),
        }

        # Skip trace
        skip_trace = (
            db.query(SkipTrace)
            .filter(SkipTrace.property_id == prop.id)
            .order_by(SkipTrace.created_at.desc())
            .first()
        )
        if skip_trace:
            signals["skip_trace"] = {
                "has_owner_name": bool(
                    skip_trace.owner_name
                    and skip_trace.owner_name != "Unknown Owner"
                ),
                "has_phone": bool(skip_trace.phone_numbers),
                "phone_count": len(skip_trace.phone_numbers)
                if skip_trace.phone_numbers
                else 0,
                "has_email": bool(skip_trace.emails),
                "email_count": len(skip_trace.emails) if skip_trace.emails else 0,
            }

        # Activity velocity (last 7 days vs 7-14 days ago)
        cutoff_7d = datetime.now(timezone.utc) - timedelta(days=7)
        cutoff_14d = datetime.now(timezone.utc) - timedelta(days=14)

        activity_7d = (
            db.query(ConversationHistory)
            .filter(
                ConversationHistory.property_id == prop.id,
                ConversationHistory.created_at >= cutoff_7d,
            )
            .count()
        )
        activity_7_14d = (
            db.query(ConversationHistory)
            .filter(
                ConversationHistory.property_id == prop.id,
                ConversationHistory.created_at >= cutoff_14d,
                ConversationHistory.created_at < cutoff_7d,
            )
            .count()
        )

        signals["activity"] = {
            "actions_last_7d": activity_7d,
            "actions_7_14d_ago": activity_7_14d,
            "accelerating": activity_7d > activity_7_14d * 1.5,
            "stagnant": activity_7d == 0 and activity_7_14d == 0,
            "notes_count": (
                db.query(PropertyNote)
                .filter(PropertyNote.property_id == prop.id)
                .count()
            ),
        }

        # Offers
        offers = (
            db.query(Offer)
            .filter(Offer.property_id == prop.id)
            .order_by(Offer.created_at.desc())
            .all()
        )
        active_offers = [o for o in offers if o.status == OfferStatus.PENDING]
        rejected_offers = [o for o in offers if o.status == OfferStatus.REJECTED]

        signals["offers"] = {
            "total_offers": len(offers),
            "active_offers": len(active_offers),
            "rejected_offers": len(rejected_offers),
            "has_recent_activity": bool(
                offers and (datetime.now(timezone.utc) - offers[0].created_at).days < 7
            ),
        }

        return signals

    def _calculate_closing_probability(self, signals: dict[str, Any]) -> dict[str, Any]:
        """Calculate closing probability from signals using weighted scoring."""
        score = 50.0  # Base score
        factors = []
        risk_factors = []
        strengths = []

        # Deal score (35% weight) - strongest signal
        deal_score = signals.get("deal_score", {}).get("score")
        if deal_score is not None:
            # Scale deal score to 0-35 contribution
            contribution = (deal_score / 100) * 35
            score += contribution - 17.5  # Centered around 50
            factors.append(f"Deal score: {deal_score}/100")
            if deal_score >= 80:
                strengths.append("Excellent deal score")
            elif deal_score < 50:
                risk_factors.append("Low deal score indicates weak opportunity")

        # Contract completion (25%)
        contracts = signals.get("contracts", {})
        completion_rate = contracts.get("completion_rate", 0)
        if contracts.get("required_total", 0) > 0:
            contribution = (completion_rate / 100) * 25
            score += contribution - 12.5
            factors.append(f"Contract completion: {completion_rate:.0f}%")
            if completion_rate >= 80:
                strengths.append("Most contracts completed")
            elif completion_rate < 50 and contracts.get("required_total", 0) > 0:
                risk_factors.append("Many required contracts outstanding")

        # Contact coverage (15%)
        contacts = signals.get("contacts", {})
        if contacts.get("has_key_roles"):
            score += 7.5
            strengths.append("Key stakeholders identified")
        else:
            score -= 7.5
            risk_factors.append("Missing key contacts (buyer/seller)")

        # Skip trace reachability (10%)
        skip_trace = signals.get("skip_trace", {})
        if skip_trace.get("has_phone") and skip_trace.get("has_email"):
            score += 5.0
            strengths.append("Owner contact info available")
        elif not skip_trace:
            score -= 5.0
            risk_factors.append("No skip trace data - can't reach owner")

        # Activity acceleration (10%)
        activity = signals.get("activity", {})
        if activity.get("accelerating"):
            score += 5.0
            strengths.append("Activity accelerating")
        elif activity.get("stagnant"):
            score -= 5.0
            risk_factors.append("No recent activity - deal may be stalled")

        # Zillow enrichment (5%)
        enrichment = signals.get("enrichment", {})
        if enrichment.get("has_zestimate"):
            spread = enrichment.get("zestimate_spread_pct")
            if spread and spread > 10:
                score += 2.5
                strengths.append(f"Strong Zestimate spread ({spread:.0f}%)")
        else:
            score -= 2.5
            risk_factors.append("Missing market data")

        # Offer activity (bonus)
        offers = signals.get("offers", {})
        if offers.get("active_offers", 0) > 0:
            score += 5.0
            strengths.append("Active offers in negotiation")
        elif offers.get("rejected_offers", 0) > 2:
            score -= 5.0
            risk_factors.append("Multiple rejected offers")

        # Normalize to 0-1 range
        probability = max(0.0, min(1.0, score / 100))

        # Determine confidence based on data completeness
        data_completeness = 0
        if signals.get("deal_score", {}).get("score"):
            data_completeness += 30
        if signals.get("contracts", {}).get("total_contracts", 0) > 0:
            data_completeness += 25
        if signals.get("enrichment"):
            data_completeness += 25
        if signals.get("skip_trace"):
            data_completeness += 20

        if data_completeness >= 75:
            confidence = "high"
        elif data_completeness >= 50:
            confidence = "medium"
        else:
            confidence = "low"

        # Estimate days to close (based on status and completion)
        status = signals.get("property", {}).get("status")
        completion_rate = contracts.get("completion_rate", 0)

        if status == PropertyStatus.NEW_PROPERTY.value:
            estimated_days = 45
        elif status == PropertyStatus.ENRICHED.value:
            estimated_days = 35
        elif status == PropertyStatus.RESEARCHED.value:
            estimated_days = 25
        elif status == PropertyStatus.WAITING_FOR_CONTRACTS.value:
            # Estimate based on completion
            remaining = max(0, 100 - completion_rate) / 100
            estimated_days = int(remaining * 20)
        else:  # COMPLETE
            estimated_days = 0

        return {
            "probability": round(probability, 2),
            "confidence": confidence,
            "estimated_days": estimated_days,
            "risk_factors": risk_factors,
            "strengths": strengths,
            "scoring_factors": factors,
        }

    def _generate_recommendations(
        self, prop: Property, signals: dict, prediction: dict
    ) -> list[dict[str, str]]:
        """Generate action recommendations based on weak signals."""
        recommendations = []

        # Check for missing enrichment
        if not signals.get("enrichment"):
            recommendations.append({
                "action": "enrich_property",
                "priority": "high",
                "reason": "Missing Zillow data - need market intelligence",
                "expected_impact": "+10-15% closing probability",
            })

        # Check for missing skip trace
        if not signals.get("skip_trace"):
            recommendations.append({
                "action": "skip_trace_property",
                "priority": "high",
                "reason": "Can't close without owner contact info",
                "expected_impact": "+20% closing probability",
            })

        # Check for missing contracts
        if signals.get("contracts", {}).get("total_contracts", 0) == 0:
            recommendations.append({
                "action": "attach_required_contracts",
                "priority": "medium",
                "reason": "No contracts attached - need to start paperwork",
                "expected_impact": "+15% closing probability",
            })

        # Check for missing key contacts
        if not signals.get("contacts", {}).get("has_key_roles"):
            recommendations.append({
                "action": "add_contact",
                "priority": "high",
                "reason": "Missing buyer/seller contacts - can't proceed",
                "expected_impact": "+25% closing probability",
            })

        # Check for stagnation
        if signals.get("activity", {}).get("stagnant"):
            recommendations.append({
                "action": "make_property_phone_call",
                "priority": "medium",
                "reason": "Deal is stagnant - need to re-engage",
                "expected_impact": "+10% closing probability",
            })

        # If no critical gaps, suggest progression
        if not recommendations and prediction["probability"] > 0.7:
            recommendations.append({
                "action": "check_property_contract_readiness",
                "priority": "low",
                "reason": "Deal looks good - verify readiness to close",
                "expected_impact": "Confirm closing timeline",
            })

        return recommendations

    async def _llm_recommend_action(
        self, prop: Property, state: dict, prediction: dict, context: str | None
    ) -> dict[str, Any]:
        """Use LLM to reason about the best next action."""
        prompt = f"""You are an expert real estate advisor. Given the following property state, recommend the single best next action.

Property: {prop.address} in {prop.city}, {prop.state}
Price: ${prop.price:,.0f}
Status: {prop.status.value if prop.status else 'N/A'}
Deal Score: {state.get('deal_score', 'N/A')}
Closing Probability: {prediction.get('closing_probability', 0)*100:.0f}%

Current State:
- Contracts: {state.get('contracts', {})}
- Contacts: {state.get('contacts', {})}
- Skip Trace: {state.get('skip_trace', {})}
- Activity: {state.get('activity', {})}

Risk Factors: {', '.join(prediction.get('risk_factors', []) or ['None'])}
Strengths: {', '.join(prediction.get('strengths', []) or ['None'])}

Context: {context or 'General progression'}

Return a JSON object with:
{{
    "action": "one of: enrich_property, skip_trace_property, attach_required_contracts, add_contact, make_property_phone_call, check_property_contract_readiness, generate_property_recap, score_property",
    "reasoning": "2-3 sentences explaining why this action is best",
    "priority": "high | medium | low",
    "expected_impact": "1 sentence on expected outcome",
    "probability_improvement": estimated percentage points this action will improve closing probability (be realistic)
}}

Return ONLY the JSON, no other text."""

        try:
            response = await llm_service.agenerate(
                prompt, model="claude-3-5-sonnet-20241022", max_tokens=500
            )

            # Parse JSON from response
            import json

            # Extract JSON if there's extra text
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                recommendation = json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")

            # Add voice summary
            recommendation["voice_summary"] = (
                f"I recommend {recommendation['action']}. {recommendation['reasoning']} "
                f"This is {recommendation['priority']} priority and should {recommendation['expected_impact']}."
            )

            return recommendation

        except Exception as e:
            logger.error(f"LLM recommendation failed: {e}")
            # Fallback to rule-based
            return {
                "action": "enrich_property",
                "reasoning": "Default to enrichment when LLM unavailable",
                "priority": "medium",
                "expected_impact": "Will gather market data",
                "voice_summary": "Recommend enriching the property with market data.",
            }

    async def _assess_property_state(
        self, db: Session, prop: Property
    ) -> dict[str, Any]:
        """Quick assessment of property state for action recommendation."""
        state = {
            "deal_score": prop.deal_score,
            "status": prop.status.value if prop.status else None,
        }

        # Count contracts
        contracts = (
            db.query(Contract).filter(Contract.property_id == prop.id).count()
        )
        state["contracts"] = contracts

        # Count contacts
        contacts = (
            db.query(Contact).filter(Contact.property_id == prop.id).count()
        )
        state["contacts"] = contacts

        # Check enrichment
        enrichment = (
            db.query(ZillowEnrichment)
            .filter(ZillowEnrichment.property_id == prop.id)
            .first()
        )
        state["has_enrichment"] = enrichment is not None

        # Check skip trace
        skip_trace = (
            db.query(SkipTrace)
            .filter(SkipTrace.property_id == prop.id)
            .first()
        )
        state["has_skip_trace"] = skip_trace is not None

        return state

    def _build_prediction_voice_summary(
        self, prop: Property, prediction: dict, recommendations: list[dict]
    ) -> str:
        """Build natural language summary of prediction."""
        prob_pct = prediction["probability"] * 100
        confidence = prediction["confidence"]

        parts = [
            f"Property {prop.address} has a {prob_pct:.0f}% probability of closing, "
            f"with {confidence} confidence."
        ]

        if prediction["strengths"]:
            parts.append(f"Strengths: {', '.join(prediction['strengths'][:2])}.")

        if prediction["risk_factors"]:
            parts.append(f"Risks: {', '.join(prediction['risk_factors'][:2])}.")

        if recommendations:
            top_rec = recommendations[0]
            parts.append(
                f"Recommended action: {top_rec['action']} - {top_rec['reason']}"
            )

        return " ".join(parts)


predictive_intelligence_service = PredictiveIntelligenceService()
