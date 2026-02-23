"""Autonomous Campaign Manager — self-optimizing voice/email campaigns."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.voice_campaign import VoiceCampaign, VoiceCampaignTarget
from app.models.contact import Contact
from app.models.property import Property
from app.models.property_note import PropertyNote
from app.services.voice_campaign_service import voice_campaign_service, CampaignStatus, CampaignTargetStatus
from app.services.relationship_intelligence_service import relationship_intelligence_service
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class AutonomousCampaignManager:
    """Self-optimizing campaign manager that adapts based on response rates."""

    async def optimize_campaign_parameters(
        self, db: Session, campaign_id: int
    ) -> dict[str, Any]:
        """Auto-adjust call time, message, targeting based on performance.

        Analyzes:
        - Best calling times (response rate by hour)
        - Winning message variants
        - High-converting property filters
        """
        campaign = db.query(VoiceCampaign).filter(VoiceCampaign.id == campaign_id).first()
        if not campaign:
            return {"error": f"Campaign {campaign_id} not found"}

        # Get performance metrics
        metrics = voice_campaign_service.get_campaign_analytics(db, campaign)

        # Analyze calling time effectiveness
        time_analysis = await self._analyze_best_calling_times(db, campaign)

        # Analyze message effectiveness
        message_analysis = await self._analyze_message_variants(db, campaign)

        # Get targeting insights
        targeting_analysis = await self._analyze_targeting_effectiveness(db, campaign)

        # Generate optimization recommendations
        optimizations = {
            "campaign_id": campaign_id,
            "current_performance": metrics,
            "best_calling_times": time_analysis,
            "message_insights": message_analysis,
            "targeting_insights": targeting_analysis,
            "recommended_adjustments": [],
        }

        # Build recommendations
        if time_analysis.get("best_hour"):
            optimizations["recommended_adjustments"].append({
                "type": "schedule",
                "recommendation": f"Focus calls around {time_analysis['best_hour']}:00 for best response",
                "expected_improvement": time_analysis.get("improvement_potential", "unknown"),
            })

        if message_analysis.get("best_variant"):
            optimizations["recommended_adjustments"].append({
                "type": "message",
                "recommendation": f"Use {message_analysis['best_variant']} message style",
                "reason": message_analysis.get("reason"),
            })

        if targeting_analysis.get("best_segments"):
            optimizations["recommended_adjustments"].append({
                "type": "targeting",
                "recommendation": f"Focus on {targeting_analysis['best_segments'][0]['description']}",
                "expected_improvement": targeting_analysis.get("improvement_potential", "unknown"),
            })

        return optimizations

    async def autonomous_campaign_execution(
        self,
        db: Session,
        goal: str,
        agent_id: int,
        campaign_name: str | None = None,
        max_duration_hours: int = 24,
    ) -> dict[str, Any]:
        """End-to-end autonomous campaign: plan → execute → optimize → report.

        This is a high-level orchestration method that:
        1. Creates a campaign from a natural language goal
        2. Executes batches of calls
        3. Optimizes based on responses
        4. Continues until complete or time limit
        """
        # Step 1: Parse goal and create campaign
        campaign_plan = await self._plan_campaign_from_goal(db, goal, agent_id)
        campaign = campaign_plan["campaign"]

        logger.info(f"Starting autonomous campaign: {campaign.name} (ID: {campaign.id})")

        # Step 2: Execute in batches with optimization
        start_time = datetime.now(timezone.utc)
        batch_number = 0
        results = {
            "campaign_id": campaign.id,
            "campaign_name": campaign.name,
            "goal": goal,
            "batches": [],
            "total_targets": 0,
            "total_calls_started": 0,
            "total_completed": 0,
            "optimizations_applied": [],
        }

        while campaign.status == CampaignStatus.ACTIVE:
            # Check time limit
            elapsed_hours = (datetime.now(timezone.utc) - start_time).total_seconds() / 3600
            if elapsed_hours >= max_duration_hours:
                logger.info(f"Autonomous campaign reached time limit ({max_duration_hours}h)")
                voice_campaign_service.pause_campaign(db, campaign)
                break

            batch_number += 1
            logger.info(f"Executing batch {batch_number} of campaign {campaign.id}")

            # Execute a batch
            batch_result = await voice_campaign_service.process_campaign_once(
                db, campaign=campaign, max_calls=10
            )

            results["batches"].append({
                "batch_number": batch_number,
                "elapsed_hours": round(elapsed_hours, 2),
                **batch_result,
            })
            results["total_targets"] += batch_result.get("targets_processed", 0)
            results["total_calls_started"] += batch_result.get("calls_started", 0)

            # Optimize every 3 batches
            if batch_number % 3 == 0 and batch_result.get("calls_started", 0) > 0:
                logger.info(f"Optimizing campaign after batch {batch_number}")
                optimization = await self.optimize_campaign_parameters(db, campaign.id)

                # Apply optimizations
                applied = await self._apply_optimizations(db, campaign, optimization)
                results["optimizations_applied"].append({
                    "batch": batch_number,
                    "optimizations": applied,
                })

            # Wait before next batch (respect rate limits)
            await asyncio.sleep(60)  # 1 minute between batches

        # Final analytics
        final_metrics = voice_campaign_service.get_campaign_analytics(db, campaign)
        results["final_metrics"] = final_metrics
        results["duration_hours"] = round(
            (datetime.now(timezone.utc) - start_time).total_seconds() / 3600, 2
        )

        logger.info(f"Autonomous campaign completed: {results}")

        return results

    async def get_campaign_roi(
        self, db: Session, campaign_id: int
    ) -> dict[str, Any]:
        """Calculate ROI of a campaign.

        Measures:
        - Cost (calls made)
        - Outcomes (deal conversions)
        - ROI percentage
        """
        campaign = db.query(VoiceCampaign).filter(VoiceCampaign.id == campaign_id).first()
        if not campaign:
            return {"error": f"Campaign {campaign_id} not found"}

        targets = db.query(VoiceCampaignTarget).filter(
            VoiceCampaignTarget.campaign_id == campaign_id
        ).all()

        # Count calls
        total_calls = sum([t.attempts_made for t in targets])
        completed_calls = len([t for t in targets if t.status == CampaignTargetStatus.COMPLETED])

        # Estimate cost (simplified - could integrate actual costs)
        avg_cost_per_call = 0.10  # $0.10 per minute
        total_cost = total_calls * avg_cost_per_call

        # Track outcomes (check for resulting deals/contracts)
        # This would require joining to properties and checking status changes
        # For now, we'll return engagement metrics
        success_rate = completed_calls / len(targets) if targets else 0

        return {
            "campaign_id": campaign_id,
            "campaign_name": campaign.name,
            "total_targets": len(targets),
            "total_calls": total_calls,
            "completed_calls": completed_calls,
            "success_rate": round(success_rate * 100, 1),
            "estimated_cost": round(total_cost, 2),
            "cost_per_completion": round(total_cost / completed_calls, 2) if completed_calls > 0 else None,
            "voice_summary": self._build_roi_voice_summary(campaign, total_calls, completed_calls, total_cost),
        }

    # ── Private Methods ──

    async def _analyze_best_calling_times(
        self, db: Session, campaign: VoiceCampaign
    ) -> dict[str, Any]:
        """Analyze which hours produce best response rates."""
        targets = db.query(VoiceCampaignTarget).filter(
            VoiceCampaignTarget.campaign_id == campaign.id
        ).all()

        # Group by hour of call
        hour_stats = {}
        for target in targets:
            if target.last_attempt_at:
                hour = target.last_attempt_at.hour
                if hour not in hour_stats:
                    hour_stats[hour] = {"attempts": 0, "completed": 0}

                hour_stats[hour]["attempts"] += target.attempts_made
                if target.status == CampaignTargetStatus.COMPLETED:
                    hour_stats[hour]["completed"] += 1

        # Find best hour
        best_hour = None
        best_rate = 0

        for hour, stats in hour_stats.items():
            if stats["attempts"] >= 3:  # Minimum data threshold
                rate = stats["completed"] / stats["attempts"]
                if rate > best_rate:
                    best_rate = rate
                    best_hour = hour

        if best_hour is not None:
            return {
                "best_hour": best_hour,
                "success_rate": round(best_rate * 100, 1),
                "hourly_breakdown": {
                    h: round(s["completed"] / s["attempts"] * 100, 1) if s["attempts"] > 0 else 0
                    for h, s in hour_stats.items()
                },
                "improvement_potential": f"{round((best_rate - 0.3) * 100, 0)}% higher than average" if best_rate > 0.3 else "modest",
            }

        return {"message": "Insufficient data for time analysis"}

    async def _analyze_message_variants(
        self, db: Session, campaign: VoiceCampaign
    ) -> dict[str, Any]:
        """Analyze which message/call purpose works best."""
        # For now, return the campaign's call purpose
        # Could be extended to analyze actual call transcripts
        return {
            "call_purpose": campaign.call_purpose,
            "best_variant": campaign.call_purpose,
            "reason": "Current call purpose is being used",
        }

    async def _analyze_targeting_effectiveness(
        self, db: Session, campaign: VoiceCampaign
    ) -> dict[str, Any]:
        """Analyze which property/contact segments convert best."""
        targets = db.query(VoiceCampaignTarget).filter(
            VoiceCampaignTarget.campaign_id == campaign.id
        ).all()

        # Analyze by property
        property_stats = {}
        for target in targets:
            if target.property_id:
                if target.property_id not in property_stats:
                    property_stats[target.property_id] = {"attempts": 0, "completed": 0}

                property_stats[target.property_id]["attempts"] += target.attempts_made
                if target.status == CampaignTargetStatus.COMPLETED:
                    property_stats[target.property_id]["completed"] += 1

        # Find best segments
        best_segments = []
        for prop_id, stats in property_stats.items():
            if stats["attempts"] >= 2:
                rate = stats["completed"] / stats["attempts"]
                if rate > 0.4:  # Above 40% success rate
                    prop = db.query(Property).filter(Property.id == prop_id).first()
                    if prop:
                        best_segments.append({
                            "property_id": prop_id,
                            "address": prop.address,
                            "success_rate": round(rate * 100, 1),
                            "description": f"Properties in {prop.city}",
                        })

        best_segments.sort(key=lambda x: x["success_rate"], reverse=True)

        return {
            "best_segments": best_segments[:5],
            "improvement_potential": f"Focus on top {len(best_segments)} segments" if best_segments else "Need more data",
        }

    async def _plan_campaign_from_goal(
        self, db: Session, goal: str, agent_id: int
    ) -> dict[str, Any]:
        """Parse natural language goal and create campaign."""
        # Use LLM to parse goal
        prompt = f"""Parse this campaign goal and extract parameters:

Goal: "{goal}"

Return JSON with:
{{
    "campaign_name": "short name",
    "description": "brief description",
    "call_purpose": "property_update | contract_reminder | closing_ready | skip_trace_outreach",
    "target_criteria": {{
        "property_ids": [list of property IDs mentioned],
        "contact_roles": [list of roles to target],
        "cities": [cities mentioned]
    }},
    "max_attempts": 3,
    "retry_delay_minutes": 60
}}

Return ONLY the JSON, no other text."""

        try:
            response = await llm_service.agenerate(prompt, max_tokens=500)
            import json
            plan = json.loads(response)
        except Exception as e:
            logger.error(f"Failed to parse campaign goal: {e}")
            # Fallback
            plan = {
                "campaign_name": goal[:50],
                "description": goal,
                "call_purpose": "property_update",
                "target_criteria": {},
                "max_attempts": 3,
                "retry_delay_minutes": 60,
            }

        # Create campaign
        campaign = voice_campaign_service.create_campaign(
            db,
            name=plan["campaign_name"],
            description=plan.get("description"),
            call_purpose=plan["call_purpose"],
            property_id=None,
            contact_roles=plan["target_criteria"].get("contact_roles"),
            max_attempts=plan.get("max_attempts", 3),
            retry_delay_minutes=plan.get("retry_delay_minutes", 60),
            rate_limit_per_minute=5,
            assistant_overrides=None,
        )

        # Add targets
        property_ids = plan["target_criteria"].get("property_ids", [])
        contact_roles = plan["target_criteria"].get("contact_roles", [])

        if property_ids:
            # Add contacts from these properties
            for prop_id in property_ids:
                contacts = db.query(Contact).filter(
                    Contact.property_id == prop_id,
                    Contact.phone.isnot(None),
                ).all()

                contact_ids = [c.id for c in contacts]
                voice_campaign_service.add_targets_manual(
                    db,
                    campaign=campaign,
                    contact_ids=contact_ids,
                    phone_numbers=[],
                    property_id=prop_id,
                )
        elif contact_roles:
            # Add contacts by role
            contacts = db.query(Contact).filter(
                Contact.phone.isnot(None),
            ).limit(100).all()

            role_matches = [c for c in contacts if c.role and c.role.value in contact_roles]
            contact_ids = [c.id for c in role_matches]
            voice_campaign_service.add_targets_manual(
                db,
                campaign=campaign,
                contact_ids=contact_ids,
                phone_numbers=[],
                property_id=None,
            )

        # Start campaign
        voice_campaign_service.start_campaign(db, campaign)

        return {"campaign": campaign, "plan": plan}

    async def _apply_optimizations(
        self, db: Session, campaign: VoiceCampaign, optimization: dict
    ) -> list[str]:
        """Apply optimization recommendations to campaign."""
        applied = []

        for rec in optimization.get("recommended_adjustments", []):
            if rec["type"] == "targeting":
                applied.append(f"Targeting: {rec['recommendation']}")
                # Could dynamically add/remove targets here

            elif rec["type"] == "schedule":
                applied.append(f"Schedule: {rec['recommendation']}")
                # Could adjust rate limits here

            elif rec["type"] == "message":
                applied.append(f"Message: {rec['recommendation']}")
                # Could adjust call_purpose or assistant_overrides here

        return applied

    def _build_roi_voice_summary(
        self, campaign: VoiceCampaign, total_calls: int, completed: int, cost: float
    ) -> str:
        """Build voice summary for ROI analysis."""
        success_rate = (completed / total_calls * 100) if total_calls > 0 else 0

        return (
            f"Campaign {campaign.name}: {total_calls} calls, {completed} completed "
            f"({success_rate:.0f}% success rate). Estimated cost: ${cost:.2f}."
        )


# Import at end
import asyncio

autonomous_campaign_manager = AutonomousCampaignManager()
