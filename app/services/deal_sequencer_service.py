"""Multi-Property Deal Sequencer — orchestrate complex multi-property transactions."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.property import Property, PropertyStatus
from app.models.offer import Offer, OfferStatus
from app.models.contract import Contract, ContractStatus
from app.models.scheduled_task import ScheduledTask, TaskType, TaskStatus
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class DealSequencerService:
    """Orchestrate complex multi-property transactions (portfolio deals, 1031 exchanges)."""

    async def sequence_1031_exchange(
        self,
        db: Session,
        sale_property_id: int,
        target_criteria: dict[str, Any],
        agent_id: int,
    ) -> dict[str, Any]:
        """Orchestrate a 1031 exchange: identify replacements, manage timeline.

        1031 Exchange Rules:
        - Must identify replacement properties within 45 days
        - Must close on replacement within 180 days
        - Replacement value must be >= sale value
        - All proceeds must be reinvested

        Returns:
            {
                "phases": [...],
                "timeline": {...},
                "replacement_candidates": [...],
                "deadlines": [...],
                "voice_summary": "..."
            }
        """
        # Get sale property
        sale_prop = db.query(Property).filter(Property.id == sale_property_id).first()
        if not sale_prop:
            return {"error": f"Sale property {sale_property_id} not found"}

        # Calculate timeline
        exchange_start = datetime.now(timezone.utc)
        identification_deadline = exchange_start + timedelta(days=45)
        closing_deadline = exchange_start + timedelta(days=180)

        # Find replacement properties
        candidates = await self._find_replacement_properties(
            db,
            sale_prop.price,
            target_criteria,
            agent_id,
        )

        # Build sequence phases
        sequence = {
            "exchange_type": "1031_exchange",
            "sale_property": {
                "id": sale_prop.id,
                "address": sale_prop.address,
                "estimated_value": sale_prop.price,
            },
            "timeline": {
                "start_date": exchange_start.isoformat(),
                "identification_deadline": identification_deadline.isoformat(),
                "closing_deadline": closing_deadline.isoformat(),
                "days_until_identification": 45,
                "days_until_closing": 180,
            },
            "phases": [
                {
                    "phase": 1,
                    "name": "List Sale Property",
                    "deadline": (exchange_start + timedelta(days=7)).isoformat(),
                    "tasks": [
                        "List property for sale",
                        "Identify qualified intermediary",
                        "Prepare 1031 exchange documentation",
                    ],
                    "status": "pending",
                },
                {
                    "phase": 2,
                    "name": "Identify Replacements",
                    "deadline": identification_deadline.isoformat(),
                    "tasks": [
                        f"Identify up to 3 replacement properties",
                        f"Minimum reinvestment: ${sale_prop.price * 1.05:,.0f}",
                    ],
                    "candidates": candidates[:3],
                    "status": "pending",
                },
                {
                    "phase": 3,
                    "name": "Close on Replacements",
                    "deadline": closing_deadline.isoformat(),
                    "tasks": [
                        "Close on sale property",
                        "Close on replacement property(ies)",
                        "Ensure all proceeds reinvested",
                    ],
                    "status": "pending",
                },
            ],
            "replacement_candidates": candidates,
            "critical_deadlines": [
                {
                    "name": "Identification Deadline",
                    "date": identification_deadline.isoformat(),
                    "days_remaining": 45,
                    "severity": "critical",
                },
                {
                    "name": "Closing Deadline",
                    "date": closing_deadline.isoformat(),
                    "days_remaining": 180,
                    "severity": "critical",
                },
            ],
        }

        # Create automated reminders
        await self._create_1031_reminders(db, sale_property_id, sequence["timeline"], agent_id)

        return {
            "sequence": sequence,
            "voice_summary": self._build_1031_voice_summary(sale_prop, candidates, sequence["timeline"]),
        }

    async def sequence_portfolio_acquisition(
        self,
        db: Session,
        property_ids: list[int],
        agent_id: int,
        strategy: str = "parallel",
    ) -> dict[str, Any]:
        """Orchestrate buying multiple properties with optimal ordering.

        Args:
            property_ids: Properties to acquire
            agent_id: Agent orchestrating the acquisition
            strategy: "parallel" (all at once) or "sequential" (one by one)

        Returns:
            {
                "acquisition_sequence": [...],
                "total_investment": float,
                "estimated_timeline_days": int,
                "contingencies": [...],
                "voice_summary": "..."
            }
        """
        # Get properties
        properties = (
            db.query(Property)
            .filter(Property.id.in_(property_ids))
            .all()
        )

        if len(properties) != len(property_ids):
            return {"error": "Some properties not found"}

        # Prioritize acquisition order
        prioritized = await self._prioritize_acquisition_order(db, properties)

        # Build sequence
        sequence = []
        total_investment = 0

        if strategy == "parallel":
            # All properties acquired simultaneously
            total_investment = sum([p.price for p in properties if p.price])

            for i, prop in enumerate(prioritized):
                sequence.append({
                    "order": i + 1,
                    "property_id": prop.id,
                    "address": prop.address,
                    "price": prop.price,
                    "can_close_parallel": True,
                    "estimated_close_days": 30,
                    "contingencies": await self._identify_contingencies(db, prop),
                })
        else:
            # Sequential acquisition
            days_offset = 0
            for i, prop in enumerate(prioritized):
                close_days = 30 + days_offset
                total_investment += prop.price or 0

                sequence.append({
                    "order": i + 1,
                    "property_id": prop.id,
                    "address": prop.address,
                    "price": prop.price,
                    "can_close_parallel": False,
                    "estimated_close_days": close_days,
                    "contingencies": await self._identify_contingencies(db, prop),
                    "parallel_actions": await self._find_parallelizable_actions(
                        db, prop, [p for p in properties if p.id != prop.id]
                    ),
                })

                days_offset += 15  # 2 weeks between closings

        # Calculate total timeline
        estimated_days = 30 if strategy == "parallel" else 30 + (len(properties) - 1) * 15

        return {
            "strategy": strategy,
            "total_properties": len(properties),
            "total_investment": round(total_investment, 2),
            "estimated_timeline_days": estimated_days,
            "acquisition_sequence": sequence,
            "voice_summary": self._build_portfolio_acquisition_voice_summary(
                len(properties), total_investment, estimated_days, strategy
            ),
        }

    async def sequence_sell_and_buy(
        self,
        db: Session,
        sale_property_id: int,
        purchase_property_id: int,
        contingency_type: str = "sale_contingent",  # or "buy_contingent"
    ) -> dict[str, Any]:
        """Orchestrate a sale-and-buy transaction with contingencies.

        Common scenario: Sell current home, buy new one, with contingency
        that sale must close before purchase closes (or vice versa).
        """
        sale_prop = db.query(Property).filter(Property.id == sale_property_id).first()
        purchase_prop = db.query(Property).filter(Property.id == purchase_property_id).first()

        if not sale_prop or not purchase_prop:
            return {"error": "One or both properties not found"}

        # Build timeline
        timeline_start = datetime.now(timezone.utc)

        sequence = {
            "contingency_type": contingency_type,
            "sale_property": {
                "id": sale_prop.id,
                "address": sale_prop.address,
                "price": sale_prop.price,
            },
            "purchase_property": {
                "id": purchase_prop.id,
                "address": purchase_prop.address,
                "price": purchase_prop.price,
            },
            "timeline": {},
        }

        if contingency_type == "sale_contingent":
            # Purchase depends on sale closing
            sequence["timeline"] = {
                "phase_1": {
                    "name": "List and Market Sale Property",
                    "deadline": (timeline_start + timedelta(days=30)).isoformat(),
                    "property": "sale",
                },
                "phase_2": {
                    "name": "Close on Sale Property",
                    "deadline": (timeline_start + timedelta(days=60)).isoformat(),
                    "property": "sale",
                    "triggers_phase_3": True,
                },
                "phase_3": {
                    "name": "Close on Purchase Property",
                    "deadline": (timeline_start + timedelta(days=75)).isoformat(),
                    "property": "purchase",
                    "contingent_on": "sale_closed",
                },
            }
        else:
            # Sale depends on purchase closing (less common)
            sequence["timeline"] = {
                "phase_1": {
                    "name": "Make Offer on Purchase (Sale Contingent)",
                    "deadline": (timeline_start + timedelta(days=7)).isoformat(),
                    "property": "purchase",
                },
                "phase_2": {
                    "name": "Close on Purchase Property",
                    "deadline": (timeline_start + timedelta(days=45)).isoformat(),
                    "property": "purchase",
                },
                "phase_3": {
                    "name": "Move and List Sale Property",
                    "deadline": (timeline_start + timedelta(days=75)).isoformat(),
                    "property": "sale",
                    "contingent_on": "purchase_closed",
                },
            }

        return {
            "sequence": sequence,
            "voice_summary": self._build_sell_buy_voice_summary(
                sale_prop, purchase_prop, contingency_type
            ),
        }

    # ── Private Methods ──

    async def _find_replacement_properties(
        self,
        db: Session,
        min_value: float,
        criteria: dict[str, Any],
        agent_id: int,
    ) -> list[dict[str, Any]]:
        """Find replacement properties for 1031 exchange."""
        # Must be >= min_value * 1.05 (equal or greater value rule)
        min_replacement_value = min_value * 1.05

        query = (
            db.query(Property)
            .filter(Property.agent_id == agent_id)
            .filter(Property.status != PropertyStatus.COMPLETE)
            .filter(Property.price >= min_replacement_value)
        )

        # Apply criteria
        if criteria.get("cities"):
            query = query.filter(Property.city.in_(criteria["cities"]))

        if criteria.get("property_types"):
            from app.models.property import PropertyType
            type_enums = [PropertyType(t) for t in criteria["property_types"]]
            query = query.filter(Property.property_type.in_(type_enums))

        if criteria.get("max_price"):
            query = query.filter(Property.price <= criteria["max_price"])

        properties = query.limit(10).all()

        return [
            {
                "property_id": p.id,
                "address": p.address,
                "city": p.city,
                "price": p.price,
                "above_minimum_pct": round((p.price / min_replacement_value - 1) * 100, 1) if min_replacement_value > 0 else 0,
                "property_type": p.property_type.value if p.property_type else None,
            }
            for p in properties
        ]

    async def _prioritize_acquisition_order(
        self, db: Session, properties: list[Property]
    ) -> list[Property]:
        """Prioritize properties for acquisition order."""
        # Sort by: highest deal score, then highest price
        prioritized = sorted(
            properties,
            key=lambda p: (p.deal_score or 0, p.price or 0),
            reverse=True,
        )
        return prioritized

    async def _identify_contingencies(
        self, db: Session, prop: Property
    ) -> list[str]:
        """Identify contingencies for a property."""
        contingencies = []

        # Check for required contracts
        contracts = (
            db.query(Contract)
            .filter(Contract.property_id == prop.id)
            .filter(Contract.is_required == True)
            .filter(Contract.status != ContractStatus.COMPLETED)
            .all()
        )

        if contracts:
            contingencies.append(f"{len(contracts)} outstanding contracts")

        # Check for offers
        offers = (
            db.query(Offer)
            .filter(Offer.property_id == prop.id)
            .filter(Offer.status == OfferStatus.PENDING)
            .all()
        )

        if offers:
            contingencies.append("Offer negotiation in progress")

        return contingencies

    async def _find_parallelizable_actions(
        self, db: Session, prop: Property, other_properties: list[Property]
    ) -> list[str]:
        """Find actions that can be done in parallel across properties."""
        parallel_actions = []

        # Inspections can be done in parallel
        parallel_actions.append("Property inspections")

        # Appraisals can be done in parallel
        parallel_actions.append("Appraisals")

        # Title searches can be done in parallel
        parallel_actions.append("Title searches")

        # Financing can be arranged for multiple properties
        parallel_actions.append("Financing arrangements")

        return parallel_actions

    async def _create_1031_reminders(
        self,
        db: Session,
        property_id: int,
        timeline: dict,
        agent_id: int,
    ):
        """Create automated reminders for 1031 exchange deadlines."""
        # Identification deadline reminder (7 days before)
        identification_date = datetime.fromisoformat(timeline["identification_deadline"])
        reminder_1 = ScheduledTask(
            property_id=property_id,
            agent_id=agent_id,
            task_type=TaskType.REMINDER,
            title="1031 Exchange: Identification Deadline Approaching",
            description="You have 7 days to identify replacement properties for your 1031 exchange",
            due_date=identification_date - timedelta(days=7),
            status=TaskStatus.PENDING,
        )
        db.add(reminder_1)

        # Closing deadline reminder (30 days before)
        closing_date = datetime.fromisoformat(timeline["closing_deadline"])
        reminder_2 = ScheduledTask(
            property_id=property_id,
            agent_id=agent_id,
            task_type=TaskType.REMINDER,
            title="1031 Exchange: Closing Deadline Approaching",
            description="You have 30 days to close on your replacement property",
            due_date=closing_date - timedelta(days=30),
            status=TaskStatus.PENDING,
        )
        db.add(reminder_2)

        db.commit()

        logger.info(f"Created 1031 exchange reminders for property {property_id}")

    def _build_1031_voice_summary(
        self, sale_prop: Property, candidates: list, timeline: dict
    ) -> str:
        """Build voice summary for 1031 exchange sequence."""
        parts = [
            f"1031 exchange for {sale_prop.address} (${sale_prop.price:,.0f})",
            f"Identification deadline: {timeline['days_until_identification']} days",
        ]

        if candidates:
            parts.append(f"Found {len(candidates)} replacement properties")
            top_candidate = candidates[0]
            parts.append(f"Top candidate: {top_candidate['address']} at ${top_candidate['price']:,.0f}")

        return ". ".join(parts) + "."

    def _build_portfolio_acquisition_voice_summary(
        self, count: int, investment: float, days: int, strategy: str
    ) -> str:
        """Build voice summary for portfolio acquisition."""
        return (
            f"Acquiring {count} properties {strategy} "
            f"for ${investment:,.0f} total investment. "
            f"Estimated timeline: {days} days."
        )

    def _build_sell_buy_voice_summary(
        self, sale_prop: Property, purchase_prop: Property, contingency: str
    ) -> str:
        """Build voice summary for sell-and-buy sequence."""
        return (
            f"{contingency.replace('_', ' ')} transaction: "
            f"selling {sale_prop.address} and buying {purchase_prop.address}."
        )


deal_sequencer_service = DealSequencerService()
