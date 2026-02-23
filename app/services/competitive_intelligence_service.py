"""Competitive Intelligence — monitor competing agents/buyers in target markets."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.property import Property, PropertyStatus, PropertyType
from app.models.offer import Offer, OfferStatus
from app.models.contract import Contract, ContractStatus
from app.models.zillow_enrichment import ZillowEnrichment
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class CompetitiveIntelligenceService:
    """Monitor competing agents and buyers in target markets."""

    async def analyze_market_competition(
        self,
        db: Session,
        city: str,
        state: str,
        property_type: str | None = None,
        days_back: int = 90,
    ) -> dict[str, Any]:
        """Analyze competing agents in a specific market.

        Returns:
            {
                "most_active_agents": [...],
                "fastest_closers": [...],
                "highest_spenders": [...],
                "winning_bid_patterns": {...},
                "voice_summary": "..."
            }
        """
        # Get recent sales/activity in this market
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)

        query = (
            db.query(Property)
            .filter(Property.city == city)
            .filter(Property.state == state)
            .filter(Property.status == PropertyStatus.COMPLETE)
            .filter(Property.updated_at >= cutoff_date)
        )

        if property_type:
            try:
                prop_type_enum = PropertyType(property_type)
                query = query.filter(Property.property_type == prop_type_enum)
            except ValueError:
                pass

        properties = query.all()

        if len(properties) < 3:
            return {
                "city": city,
                "state": state,
                "message": f"Insufficient data for competition analysis (only {len(properties)} completed deals)",
            }

        # Analyze agent activity
        agent_stats = {}
        for prop in properties:
            agent_id = prop.agent_id
            if agent_id not in agent_stats:
                agent_stats[agent_id] = {
                    "agent_id": agent_id,
                    "deal_count": 0,
                    "total_volume": 0,
                    "average_price": 0,
                    "days_to_close": [],
                }

            agent_stats[agent_id]["deal_count"] += 1
            agent_stats[agent_id]["total_volume"] += prop.price or 0

            # Calculate days to close
            if prop.created_at and prop.updated_at:
                days = (prop.updated_at - prop.created_at).days
                agent_stats[agent_id]["days_to_close"].append(days)

        # Compute averages
        for agent_id, stats in agent_stats.items():
            if stats["deal_count"] > 0:
                stats["average_price"] = stats["total_volume"] / stats["deal_count"]
            if stats["days_to_close"]:
                stats["avg_days_to_close"] = sum(stats["days_to_close"]) / len(stats["days_to_close"])

        # Rank agents
        most_active = sorted(agent_stats.values(), key=lambda x: x["deal_count"], reverse=True)[:5]

        fastest_closers = [
            a for a in agent_stats.values() if a.get("avg_days_to_close")
        ]
        fastest_closers.sort(key=lambda x: x["avg_days_to_close"])[:5]

        highest_spenders = sorted(agent_stats.values(), key=lambda x: x["total_volume"], reverse=True)[:5]

        # Analyze winning bid patterns
        winning_patterns = await self._analyze_bidding_patterns(db, [p.id for p in properties])

        return {
            "city": city,
            "state": state,
            "property_type": property_type,
            "period_days": days_back,
            "total_deals_analyzed": len(properties),
            "active_agents_count": len(agent_stats),
            "most_active_agents": [
                {
                    "agent_id": a["agent_id"],
                    "deals_closed": a["deal_count"],
                    "total_volume": round(a["total_volume"], 2),
                }
                for a in most_active
            ],
            "fastest_closers": [
                {
                    "agent_id": a["agent_id"],
                    "avg_days_to_close": round(a["avg_days_to_close"], 1),
                    "deals_closed": a["deal_count"],
                }
                for a in fastest_closers
            ],
            "highest_spenders": [
                {
                    "agent_id": a["agent_id"],
                    "total_volume": round(a["total_volume"], 2),
                    "deals_closed": a["deal_count"],
                }
                for a in highest_spenders
            ],
            "winning_bid_patterns": winning_patterns,
            "voice_summary": self._build_competition_voice_summary(
                city, len(properties), len(agent_stats), most_active[0] if most_active else None
            ),
        }

    async def detect_competitive_activity(
        self,
        db: Session,
        property_id: int,
    ) -> dict[str, Any]:
        """Alert if competition is interested in the same property.

        Monitors:
        - Viewing activity spikes
        - Multiple offers
        - Price acceleration
        """
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            return {"error": f"Property {property_id} not found"}

        signals = {}
        urgency = "normal"

        # Check for multiple offers
        offers = (
            db.query(Offer)
            .filter(Offer.property_id == property_id)
            .all()
        )

        if len(offers) > 1:
            signals["multiple_offers"] = {
                "count": len(offers),
                "severity": "high" if len(offers) > 3 else "medium",
            }
            urgency = "high"

        # Check for recent price changes
        enrichment = (
            db.query(ZillowEnrichment)
            .filter(ZillowEnrichment.property_id == property_id)
            .first()
        )

        if enrichment and enrichment.price_history:
            # Check if price increased recently
            recent_changes = [
                p for p in enrichment.price_history[-5:]
                if p.get("event") == "Price change"
            ]

            if recent_changes:
                # Calculate trend
                if len(recent_changes) >= 2:
                    latest = recent_changes[0].get("price", 0)
                    previous = recent_changes[-1].get("price", 0)
                    if previous > 0 and latest > previous:
                        increase_pct = (latest - previous) / previous * 100
                        if increase_pct > 5:
                            signals["price_acceleration"] = {
                                "increase_pct": round(increase_pct, 1),
                                "severity": "high" if increase_pct > 10 else "medium",
                            }
                            urgency = "high"

        # Check for rapid status changes
        if prop.created_at:
            days_since_creation = (datetime.now(timezone.utc) - prop.created_at).days
            if days_since_creation < 7 and prop.status != PropertyStatus.NEW_PROPERTY:
                signals["rapid_progression"] = {
                    "days_to_current_status": days_since_creation,
                    "severity": "medium",
                }
                if urgency == "normal":
                    urgency = "medium"

        # Generate alert if signals detected
        if signals:
            return {
                "property_id": property_id,
                "address": prop.address,
                "alert": "Competitive activity detected",
                "urgency": urgency,
                "signals_detected": list(signals.keys()),
                "signals": signals,
                "recommended_action": self._suggest_competitive_action(urgency, signals),
                "voice_summary": self._build_competitive_activity_voice_summary(
                    prop, urgency, signals
                ),
            }

        return {
            "property_id": property_id,
            "address": prop.address,
            "message": "No significant competitive activity detected",
            "urgency": "low",
            "voice_summary": f"No signs of competing interest in {prop.address}",
        }

    async def get_market_saturation(
        self,
        db: Session,
        city: str,
        state: str,
        property_type: str | None = None,
    ) -> dict[str, Any]:
        """Analyze market saturation - inventory levels and demand.

        Returns:
            {
                "inventory_level": "low" | "medium" | "high",
                "days_on_market_avg": int,
                "price_trend": "rising" | "stable" | "falling",
                "buyers_per_property": float,
                "voice_summary": "..."
            }
        """
        # Get active inventory
        query = (
            db.query(Property)
            .filter(Property.city == city)
            .filter(Property.state == state)
            .filter(Property.status != PropertyStatus.COMPLETE)
        )

        if property_type:
            try:
                prop_type_enum = PropertyType(property_type)
                query = query.filter(Property.property_type == prop_type_enum)
            except ValueError:
                pass

        active_properties = query.all()

        # Get recently sold (last 90 days) for demand analysis
        cutoff = datetime.now(timezone.utc) - timedelta(days=90)
        sold_properties = (
            db.query(Property)
            .filter(Property.city == city)
            .filter(Property.state == state)
            .filter(Property.status == PropertyStatus.COMPLETE)
            .filter(Property.updated_at >= cutoff)
        )

        if property_type:
            sold_properties = sold_properties.filter(Property.property_type == prop_type_enum)

        sold_properties = sold_properties.all()

        # Calculate metrics
        inventory_count = len(active_properties)
        sold_count = len(sold_properties)

        # Days on market average
        dom_values = []
        for prop in active_properties:
            if prop.created_at:
                dom = (datetime.now(timezone.utc) - prop.created_at).days
                dom_values.append(dom)

        avg_dom = sum(dom_values) / len(dom_values) if dom_values else 0

        # Determine inventory level
        if sold_count > 0:
            months_of_supply = inventory_count / (sold_count / 3)  # 90 days = 3 months
            if months_of_supply < 3:
                inventory_level = "low"
            elif months_of_supply < 6:
                inventory_level = "medium"
            else:
                inventory_level = "high"
        else:
            inventory_level = "unknown"

        # Price trend
        if sold_properties:
            recent_prices = [p.price for p in sold_properties[-10:] if p.price]
            older_prices = [p.price for p in sold_properties[:-10] if p.price]

            if recent_prices and older_prices:
                avg_recent = sum(recent_prices) / len(recent_prices)
                avg_older = sum(older_prices) / len(older_prices)

                if avg_recent > avg_older * 1.05:
                    price_trend = "rising"
                elif avg_recent < avg_older * 0.95:
                    price_trend = "falling"
                else:
                    price_trend = "stable"
            else:
                price_trend = "unknown"
        else:
            price_trend = "unknown"

        return {
            "city": city,
            "state": state,
            "property_type": property_type,
            "inventory_count": inventory_count,
            "sold_last_90_days": sold_count,
            "inventory_level": inventory_level,
            "average_days_on_market": round(avg_dom, 1) if avg_dom else None,
            "price_trend": price_trend,
            "months_of_supply": round(months_of_supply, 1) if sold_count > 0 else None,
            "market_health": self._assess_market_health(inventory_level, price_trend),
            "voice_summary": self._build_saturation_voice_summary(
                city, inventory_level, avg_dom, price_trend
            ),
        }

    # ── Private Methods ──

    async def _analyze_bidding_patterns(
        self, db: Session, property_ids: list[int]
    ) -> dict[str, Any]:
        """Analyze bidding strategies from historical data."""
        # Get offers for these properties
        offers = (
            db.query(Offer)
            .filter(Offer.property_id.in_(property_ids))
            .all()
        )

        if len(offers) < 5:
            return {"message": "Insufficient offer data for pattern analysis"}

        # Analyze offer vs list price
        offer_ratios = []
        for offer in offers:
            if offer.amount:
                prop = db.query(Property).filter(Property.id == offer.property_id).first()
                if prop and prop.price:
                    ratio = offer.amount / prop.price
                    offer_ratios.append(ratio)

        if offer_ratios:
            avg_ratio = sum(offer_ratios) / len(offer_ratios)
            max_ratio = max(offer_ratios)

            return {
                "average_offer_to_list_pct": round(avg_ratio * 100, 1),
                "highest_offer_to_list_pct": round(max_ratio * 100, 1),
                "common_strategy": "above_list" if avg_ratio > 1.0 else "below_list",
                "competition_level": "high" if avg_ratio > 1.05 else "moderate",
            }

        return {"message": "Could not analyze bidding patterns"}

    def _suggest_competitive_action(self, urgency: str, signals: dict) -> str:
        """Suggest action based on competitive signals."""
        if urgency == "high":
            return "Submit strongest offer immediately; consider escalation clause and quick close"
        elif urgency == "medium":
            return "Strengthen offer terms; be prepared to move quickly"
        else:
            return "Monitor for changes; proceed with standard offer"

    def _assess_market_health(self, inventory: str, trend: str) -> str:
        """Assess overall market health."""
        if inventory == "low" and trend == "rising":
            return "seller_market"
        elif inventory == "high" and trend == "falling":
            return "buyer_market"
        else:
            return "balanced"

    def _build_competition_voice_summary(
        self, city: str, total_deals: int, agent_count: int, top_agent: dict | None
    ) -> str:
        """Build voice summary for competition analysis."""
        parts = [f"In {city},"]

        if total_deals > 0:
            parts.append(f"{total_deals} deals closed by {agent_count} agents in the last 90 days")

        if top_agent:
            parts.append(f"Top agent closed {top_agent['deal_count']} deals")

        return ". ".join(parts) + "." if len(parts) > 1 else f"Competition analysis for {city}"

    def _build_competitive_activity_voice_summary(
        self, prop: Property, urgency: str, signals: dict
    ) -> str:
        """Build voice summary for competitive activity alert."""
        signal_desc = ", ".join([s.replace("_", " ") for s in signals.keys()])

        return (
            f"Competitive activity detected for {prop.address}. "
            f"Signals: {signal_desc}. Urgency: {urgency}. "
            f"Action: {self._suggest_competitive_action(urgency, signals)}."
        )

    def _build_saturation_voice_summary(
        self, city: str, inventory: str, dom: float, trend: str
    ) -> str:
        """Build voice summary for market saturation."""
        return (
            f"{city} has {inventory} inventory levels, "
            f"average {dom:.0f} days on market, "
            f"with {trend} prices."
        )


competitive_intelligence_service = CompetitiveIntelligenceService()
