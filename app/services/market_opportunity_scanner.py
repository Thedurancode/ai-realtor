"""Market Opportunity Scanner — finds deals matching agent's success patterns."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.property import Property, PropertyStatus, PropertyType
from app.models.agent import Agent
from app.models.zillow_enrichment import ZillowEnrichment
from app.models.deal_outcome import DealOutcome, OutcomeStatus
from app.models.market_watchlist import MarketWatchlist
from app.services.property_scoring_service import property_scoring_service
from app.services.predictive_intelligence_service import predictive_intelligence_service
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class MarketOpportunityScanner:
    """Scan for market opportunities matching agent's success patterns."""

    async def scan_market_opportunities(
        self,
        db: Session,
        agent_id: int,
        limit: int = 10,
        min_score: float = 70,
        property_types: list[str] | None = None,
        cities: list[str] | None = None,
        max_price: float | None = None,
    ) -> dict[str, Any]:
        """Find opportunities matching agent's success patterns.

        Scans active properties and returns top matches based on:
        - Agent's historical success patterns
        - High deal scores
        - Market conditions

        Returns:
            {
                "total_scanned": N,
                "opportunities": [
                    {
                        "property_id": N,
                        "address": "...",
                        "score": N,
                        "match_reason": "...",
                        "estimated_roi": "...",
                        "voice_summary": "..."
                    }
                ]
            }
        """
        # Get agent's success patterns
        patterns = await self._get_agent_patterns(db, agent_id)

        # Build base query for active properties (not complete)
        query = (
            db.query(Property)
            .filter(Property.agent_id == agent_id)
            .filter(Property.status != PropertyStatus.COMPLETE)
        )

        # Apply filters based on patterns
        if patterns.get("best_property_types") and not property_types:
            property_types = patterns["best_property_types"][:2]

        if property_types:
            type_enums = [PropertyType(t) for t in property_types if t in [e.value for e in PropertyType]]
            if type_enums:
                query = query.filter(Property.property_type.in_(type_enums))

        if patterns.get("best_cities") and not cities:
            cities = patterns["best_cities"][:2]

        if cities:
            query = query.filter(Property.city.in_(cities))

        if max_price:
            query = query.filter(Property.price <= max_price)

        # Get candidates
        properties = query.limit(50).all()

        if not properties:
            return {
                "agent_id": agent_id,
                "total_scanned": 0,
                "opportunities": [],
                "message": "No active properties match criteria",
            }

        # Score each property
        opportunities = []
        for prop in properties:
            # Get or calculate deal score
            if prop.deal_score is None:
                score_result = property_scoring_service.score_property(db, prop.id, save=True)
                deal_score = score_result.get("score", 0)
            else:
                deal_score = prop.deal_score

            # Skip if below minimum score
            if deal_score < min_score:
                continue

            # Calculate match score based on patterns
            match_score, match_reason = self._calculate_pattern_match(prop, patterns)

            # Estimate ROI
            estimated_roi = await self._estimate_roi(db, prop)

            # Build opportunity summary
            opportunity = {
                "property_id": prop.id,
                "address": prop.address,
                "city": prop.city,
                "state": prop.state,
                "price": prop.price,
                "deal_score": deal_score,
                "grade": prop.score_grade,
                "match_score": match_score,
                "match_reason": match_reason,
                "estimated_roi": estimated_roi,
                "property_type": prop.property_type.value if prop.property_type else None,
                "status": prop.status.value if prop.status else None,
            }

            # Add voice summary
            opportunity["voice_summary"] = self._build_opportunity_voice_summary(opportunity)

            opportunities.append(opportunity)

        # Sort by combined score (deal score + match score)
        opportunities.sort(
            key=lambda x: (x["deal_score"] * 0.6 + x["match_score"] * 0.4),
            reverse=True,
        )

        # Get top opportunities
        top_opportunities = opportunities[:limit]

        return {
            "agent_id": agent_id,
            "total_scanned": len(properties),
            "opportunities_found": len(opportunities),
            "top_opportunities": top_opportunities,
            "patterns_used": patterns,
            "voice_summary": self._build_scan_voice_summary(top_opportunities, patterns),
        }

    async def detect_market_shifts(
        self,
        db: Session,
        agent_id: int,
        cities: list[str] | None = None,
    ) -> dict[str, Any]:
        """Detect significant changes in market conditions.

        Monitors:
        - Price changes (drops/surges)
        - Inventory levels
        - Days on market trends
        - New comparable sales

        Returns alerts for actionable market shifts.
        """
        # Get agent's watchlist cities if not specified
        if not cities:
            watchlists = (
                db.query(MarketWatchlist)
                .filter(
                    MarketWatchlist.agent_id == agent_id,
                    MarketWatchlist.is_active == True,
                )
                .all()
            )
            cities = list(set([w.city for w in watchlists if w.city]))

        if not cities:
            return {
                "agent_id": agent_id,
                "message": "No cities to monitor. Create watchlists first.",
            }

        shifts = []

        for city in cities:
            city_shift = await self._analyze_city_market(db, city)
            if city_shift:
                shifts.append(city_shift)

        # Sort by significance
        shifts.sort(key=lambda x: x.get("significance", 0), reverse=True)

        return {
            "agent_id": agent_id,
            "cities_monitored": cities,
            "shifts_detected": len(shifts),
            "shifts": shifts,
            "voice_summary": self._build_shifts_voice_summary(shifts),
        }

    async def find_similar_deals(
        self,
        db: Session,
        property_id: int,
        agent_id: int | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Find similar properties in agent's portfolio or market.

        Useful for:
        - Comparing deal terms
        - Understanding market positioning
        - Learning from similar outcomes
        """
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            return {"error": f"Property {property_id} not found"}

        # Find similar properties
        query = db.query(Property).filter(Property.id != property_id)

        if agent_id:
            query = query.filter(Property.agent_id == agent_id)

        # Similarity criteria
        sim_criteria = []

        # Same city (strong signal)
        city_matches = (
            query.filter(Property.city == prop.city)
            .filter(Property.state == prop.state)
            .all()
        )

        # Same property type
        type_matches = (
            query.filter(Property.property_type == prop.property_type)
            .all() if prop.property_type else []
        )

        # Similar price range (±20%)
        price_min = prop.price * 0.8
        price_max = prop.price * 1.2
        price_matches = (
            query.filter(Property.price >= price_min)
            .filter(Property.price <= price_max)
            .all()
        )

        # Score similarity
        similar_props = {}
        for p in set(city_matches + type_matches + price_matches):
            if p.id == property_id:
                continue

            similarity_score = 0
            reasons = []

            if p.city == prop.city and p.state == prop.state:
                similarity_score += 40
                reasons.append("Same city")

            if p.property_type == prop.property_type:
                similarity_score += 30
                reasons.append(f"Same type ({p.property_type.value})")

            if price_min <= p.price <= price_max:
                similarity_score += 20
                reasons.append("Similar price")

            if p.deal_score and prop.deal_score:
                if abs(p.deal_score - prop.deal_score) < 10:
                    similarity_score += 10
                    reasons.append("Similar deal score")

            if similarity_score >= 40:  # Minimum threshold
                similar_props[p.id] = {
                    "property": p,
                    "similarity_score": similarity_score,
                    "reasons": reasons,
                }

        # Sort by similarity
        sorted_similar = sorted(
            similar_props.items(), key=lambda x: x[1]["similarity_score"], reverse=True
        )

        # Build results
        results = []
        for prop_id, data in sorted_similar[:limit]:
            p = data["property"]
            results.append({
                "property_id": p.id,
                "address": p.address,
                "city": p.city,
                "state": p.state,
                "price": p.price,
                "deal_score": p.deal_score,
                "grade": p.score_grade,
                "status": p.status.value if p.status else None,
                "similarity_score": data["similarity_score"],
                "similarity_reasons": data["reasons"],
            })

        return {
            "reference_property": {
                "id": prop.id,
                "address": prop.address,
                "city": prop.city,
                "price": prop.price,
                "deal_score": prop.deal_score,
            },
            "similar_properties": results,
            "voice_summary": self._build_similar_voice_summary(prop, results),
        }

    # ── Private Methods ──

    async def _get_agent_patterns(self, db: Session, agent_id: int) -> dict[str, Any]:
        """Get agent's success patterns or use defaults."""
        try:
            patterns_data = await learning_system_service.get_agent_success_patterns(
                db, agent_id, period="month"
            )

            if "best_property_types" in patterns_data:
                return {
                    "best_property_types": [
                        t["type"] for t in patterns_data.get("best_property_types", [])
                    ],
                    "best_cities": [
                        c["city"] for c in patterns_data.get("best_cities", [])
                    ],
                    "optimal_price_range": patterns_data.get("optimal_price_range"),
                }
        except Exception as e:
            logger.warning(f"Could not get agent patterns: {e}")

        # Default patterns
        return {
            "best_property_types": ["house", "condo"],
            "best_cities": [],
            "optimal_price_range": None,
        }

    def _calculate_pattern_match(self, prop: Property, patterns: dict) -> tuple[float, str]:
        """Calculate how well property matches agent's success patterns."""
        match_score = 0
        reasons = []

        # Property type match
        if prop.property_type and prop.property_type.value in patterns.get("best_property_types", []):
            match_score += 35
            reasons.append(f"Matches your success with {prop.property_type.value}s")

        # City match
        if prop.city in patterns.get("best_cities", []):
            match_score += 35
            reasons.append(f"In your top city: {prop.city}")

        # Price range match
        price_range = patterns.get("optimal_price_range")
        if price_range:
            range_name = price_range.get("range")
            # Simple check - could be more sophisticated
            if "under_300k" in str(range_name) and prop.price < 300000:
                match_score += 30
                reasons.append("In your optimal price range")
            elif "300k_500k" in str(range_name) and 300000 <= prop.price < 500000:
                match_score += 30
                reasons.append("In your optimal price range")
            elif "500k_750k" in str(range_name) and 500000 <= prop.price < 750000:
                match_score += 30
                reasons.append("In your optimal price range")

        # Deal score bonus
        if prop.deal_score and prop.deal_score >= 80:
            match_score += 20
            reasons.append("High deal score")

        if not reasons:
            reasons.append("General opportunity")

        return match_score, "; ".join(reasons)

    async def _estimate_roi(self, db: Session, prop: Property) -> dict[str, Any]:
        """Estimate ROI for this property."""
        roi = {
            "potential_upside": 0,
            "estimated_profit": 0,
            "cash_on_cash_return": 0,
        }

        # Get enrichment
        enrichment = (
            db.query(ZillowEnrichment)
            .filter(ZillowEnrichment.property_id == prop.id)
            .first()
        )

        if enrichment and enrichment.zestimate:
            upside = enrichment.zestimate - prop.price
            roi["potential_upside"] = round(upside, 2)
            roi["potential_upside_pct"] = round((upside / prop.price) * 100, 1) if prop.price > 0 else 0

        # Rental potential
        if enrichment and enrichment.rent_zestimate:
            annual_rent = enrichment.rent_zestimate * 12
            gross_yield = (annual_rent / prop.price) * 100 if prop.price > 0 else 0
            roi["annual_rental_income"] = round(annual_rent, 2)
            roi["gross_yield_pct"] = round(gross_yield, 1)

        return roi

    async def _analyze_city_market(self, db: Session, city: str) -> dict[str, Any] | None:
        """Analyze a city for market shifts."""
        # Get properties in this city
        city_props = (
            db.query(Property)
            .filter(Property.city == city)
            .filter(Property.created_at >= datetime.now(timezone.utc) - timedelta(days=30))
            .all()
        )

        if len(city_props) < 3:
            return None

        # Check for price trends
        prices = [p.price for p in city_props if p.price]
        if prices:
            avg_price = sum(prices) / len(prices)

            # Compare to historical (simplified - could use proper time windows)
            older_props = (
                db.query(Property)
                .filter(Property.city == city)
                .filter(
                    Property.created_at >= datetime.now(timezone.utc) - timedelta(days=60),
                    Property.created_at < datetime.now(timezone.utc) - timedelta(days=30),
                )
                .all()
            )

            if older_props:
                old_prices = [p.price for p in older_props if p.price]
                if old_prices:
                    old_avg = sum(old_prices) / len(old_prices)
                    change_pct = ((avg_price - old_avg) / old_avg) * 100

                    if abs(change_pct) > 10:  # Significant shift
                        significance = min(100, abs(change_pct) * 2)

                        return {
                            "city": city,
                            "shift_type": "price_drop" if change_pct < 0 else "price_surge",
                            "magnitude_pct": round(change_pct, 1),
                            "current_avg_price": round(avg_price, 2),
                            "previous_avg_price": round(old_avg, 2),
                            "significance": round(significance, 1),
                            "action": "increase_buying_activity" if change_pct < -5 else "cautious_approach",
                            "voice_summary": f"{city.title()}: {'Prices dropped' if change_pct < 0 else 'Prices surged'} {abs(change_pct):.0f}% - {'buying opportunity' if change_pct < 0 else 'market heating up'}",
                        }

        return None

    def _build_opportunity_voice_summary(self, opp: dict) -> str:
        """Build voice summary for an opportunity."""
        parts = [
            f"{opp['address']}",
            f"score {opp['deal_score']:.0f}, grade {opp.get('grade', 'N/A')}",
        ]

        if opp.get("estimated_roi", {}).get("potential_upside_pct"):
            parts.append(f"upside {opp['estimated_roi']['potential_upside_pct']:.0f}%")

        return ". ".join(parts) + "."

    def _build_scan_voice_summary(
        self, opportunities: list[dict], patterns: dict
    ) -> str:
        """Build voice summary for scan results."""
        if not opportunities:
            return "No opportunities found matching your criteria."

        count = len(opportunities)
        top = opportunities[0]

        parts = [f"Found {count} opportunities"]

        if patterns.get("best_property_types"):
            parts.append(f"matching your success with {patterns['best_property_types'][0]}s")

        if top:
            parts.append(
                f"Top opportunity: {top['address']} with score {top['deal_score']:.0f}"
            )

        return ". ".join(parts) + "."

    def _build_shifts_voice_summary(self, shifts: list[dict]) -> str:
        """Build voice summary for market shifts."""
        if not shifts:
            return "No significant market shifts detected."

        count = len(shifts)
        top_shifts = shifts[:3]

        parts = [f"Detected {count} market shifts"]

        for shift in top_shifts:
            parts.append(shift.get("voice_summary", f"{shift['city']}: {shift['shift_type']}"))

        return ". ".join(parts) + "."

    def _build_similar_voice_summary(
        self, prop: Property, similar: list[dict]
    ) -> str:
        """Build voice summary for similar properties."""
        if not similar:
            return f"No similar properties found to {prop.address}."

        count = len(similar)
        top = similar[0]

        return (
            f"Found {count} properties similar to {prop.address}. "
            f"Closest match: {top['address']} ({top['similarity_score']}% similar)."
        )


# Import at end to avoid circular dependency
from app.services.learning_system_service import learning_system_service

market_opportunity_scanner = MarketOpportunityScanner()
