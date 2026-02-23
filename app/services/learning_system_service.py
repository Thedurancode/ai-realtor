"""Adaptive Learning System — learns from outcomes to improve predictions."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.property import Property, PropertyStatus
from app.models.deal_outcome import DealOutcome, OutcomeStatus, AgentPerformanceMetrics, PredictionLog
from app.models.contact import Contact, ContactRole
from app.services.predictive_intelligence_service import predictive_intelligence_service

logger = logging.getLogger(__name__)


class LearningSystemService:
    """Learn from deal outcomes to improve predictions and recommendations."""

    async def record_outcome(
        self,
        db: Session,
        property_id: int,
        status: OutcomeStatus,
        final_sale_price: float | None = None,
        outcome_reason: str | None = None,
        lessons_learned: str | None = None,
    ) -> dict[str, Any]:
        """Record actual outcome and update predictions.

        This should be called when a deal is won/lost/withdrawn.
        It updates the DealOutcome record and back-fills PredictionLog accuracy.
        """
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            return {"error": f"Property {property_id} not found"}

        # Get or create DealOutcome
        outcome = (
            db.query(DealOutcome)
            .filter(DealOutcome.property_id == property_id)
            .first()
        )

        if not outcome:
            outcome = DealOutcome(
                property_id=property_id,
                agent_id=prop.agent_id,
                original_list_price=prop.price,
            )
            db.add(outcome)

        # Update outcome
        outcome.status = status
        outcome.final_sale_price = final_sale_price
        outcome.outcome_reason = outcome_reason
        outcome.lessons_learned = lessons_learned

        if status == OutcomeStatus.CLOSED_WON or status == OutcomeStatus.CLOSED_LOST:
            outcome.closed_at = datetime.now(timezone.utc)
            if outcome.created_at:
                outcome.days_to_close = (outcome.closed_at - outcome.created_at).days

        db.commit()

        # Back-fill prediction logs with actual outcome
        await self._update_prediction_logs(db, property_id, status, outcome.days_to_close)

        # Update agent performance metrics
        await self._update_agent_metrics(db, prop.agent_id)

        logger.info(f"Recorded outcome for property {property_id}: {status.value}")

        return {
            "property_id": property_id,
            "status": status.value,
            "outcome": outcome,
            "prediction_logs_updated": True,
        }

    async def get_agent_success_patterns(
        self, db: Session, agent_id: int, period: str = "month"
    ) -> dict[str, Any]:
        """Learn agent's success patterns from historical performance.

        Returns:
            {
                "best_property_types": [...],
                "best_cities": [...],
                "optimal_price_range": {...},
                "average_time_to_close": days,
                "closing_rate_by_type": {...},
                "success_factors": [...],
                "avoid_factors": [...]
            }
        """
        # Get completed deals for agent
        period_start = self._get_period_start(period)

        completed_deals = (
            db.query(DealOutcome)
            .filter(
                DealOutcome.agent_id == agent_id,
                DealOutcome.status.in_([OutcomeStatus.CLOSED_WON, OutcomeStatus.CLOSED_LOST]),
                DealOutcome.closed_at >= period_start,
            )
            .all()
        )

        if not completed_deals:
            return {
                "agent_id": agent_id,
                "period": period,
                "message": "Not enough completed deals for analysis",
            }

        # Analyze patterns
        won_deals = [d for d in completed_deals if d.status == OutcomeStatus.CLOSED_WON]
        lost_deals = [d for d in completed_deals if d.status == OutcomeStatus.CLOSED_LOST]

        # Get property details for each deal
        won_property_ids = [d.property_id for d in won_deals]
        lost_property_ids = [d.property_id for d in lost_deals]

        won_props = (
            db.query(Property)
            .filter(Property.id.in_(won_property_ids))
            .all() if won_property_ids else []
        )
        lost_props = (
            db.query(Property)
            .filter(Property.id.in_(lost_property_ids))
            .all() if lost_property_ids else []
        )

        # Best property types
        type_stats = self._analyze_by_property_type(won_props, lost_props)

        # Best cities
        city_stats = self._analyze_by_city(won_props, lost_props)

        # Optimal price range
        price_analysis = self._analyze_price_ranges(won_props, lost_props)

        # Average time to close
        avg_days_to_close = (
            sum([d.days_to_close for d in won_deals if d.days_to_close]) / len(won_deals)
            if won_deals
            else None
        )

        # Success/failure factors from predictions
        success_factors, avoid_factors = await self._analyze_prediction_factors(
            db, won_property_ids, lost_property_ids
        )

        return {
            "agent_id": agent_id,
            "period": period,
            "total_deals_analyzed": len(completed_deals),
            "won_deals": len(won_deals),
            "lost_deals": len(lost_deals),
            "closing_rate": len(won_deals) / len(completed_deals) if completed_deals else 0,
            "best_property_types": type_stats["best"],
            "worst_property_types": type_stats["worst"],
            "best_cities": city_stats["best"],
            "worst_cities": city_stats["worst"],
            "optimal_price_range": price_analysis["optimal"],
            "average_days_to_close": round(avg_days_to_close, 1) if avg_days_to_close else None,
            "success_factors": success_factors,
            "avoid_factors": avoid_factors,
            "voice_summary": self._build_pattern_voice_summary(
                type_stats, city_stats, price_analysis
            ),
        }

    async def evaluate_prediction_accuracy(
        self, db: Session, agent_id: int | None = None, days: int = 30
    ) -> dict[str, Any]:
        """Evaluate how accurate our predictions have been.

        Returns:
            {
                "total_predictions": N,
                "predictions_with_outcomes": N,
                "accuracy_metrics": {
                    "mean_absolute_error": MAE,
                    "directional_accuracy": %,
                    "confidence_calibration": ...
                },
                "by_confidence": {
                    "high": {...},
                    "medium": {...},
                    "low": {...}
                }
            }
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        query = db.query(PredictionLog).filter(
            PredictionLog.created_at >= cutoff_date,
            PredictionLog.actual_outcome.isnot(None),
        )

        if agent_id:
            # Join with properties to filter by agent
            query = query.join(Property).filter(Property.agent_id == agent_id)

        predictions = query.all()

        if not predictions:
            return {
                "period_days": days,
                "message": "No predictions with recorded outcomes yet",
            }

        # Calculate accuracy metrics
        probability_errors = []
        directional_correct = 0
        total = len(predictions)

        confidence_buckets = {"high": [], "medium": [], "low": []}

        for pred in predictions:
            if pred.probability_error is not None:
                probability_errors.append(abs(pred.probability_error))

            if pred.was_correct_direction is not None:
                directional_correct += pred.was_correct_direction

            # Bucket by confidence
            bucket = confidence_buckets.get(pred.confidence, [])
            if pred.probability_error is not None:
                bucket.append(abs(pred.probability_error))

        # Compute metrics
        mae = (
            sum(probability_errors) / len(probability_errors)
            if probability_errors
            else None
        )
        directional_accuracy = (directional_correct / total * 100) if total > 0 else None

        # Confidence calibration
        calibration = {}
        for conf, errors in confidence_buckets.items():
            if errors:
                calibration[conf] = {
                    "count": len(errors),
                    "mean_error": round(sum(errors) / len(errors), 3),
                }

        return {
            "period_days": days,
            "total_predictions": total,
            "predictions_with_outcomes": total,
            "accuracy_metrics": {
                "mean_absolute_error": round(mae, 3) if mae else None,
                "directional_accuracy": round(directional_accuracy, 1)
                if directional_accuracy
                else None,
            },
            "by_confidence": calibration,
            "voice_summary": self._build_accuracy_voice_summary(mae, directional_accuracy),
        }

    async def log_prediction(
        self,
        db: Session,
        property_id: int,
        predicted_probability: float,
        predicted_days: int,
        confidence: str,
        feature_snapshot: dict[str, Any],
    ) -> PredictionLog:
        """Log a prediction for later accuracy evaluation.

        This is called automatically by predictive_intelligence_service.
        """
        log = PredictionLog(
            property_id=property_id,
            predicted_probability=predicted_probability,
            predicted_days=predicted_days,
            confidence=confidence,
            feature_snapshot=feature_snapshot,
            deal_score=feature_snapshot.get("deal_score", {}).get("score"),
            completion_rate=feature_snapshot.get("contracts", {}).get("completion_rate"),
            has_contacts=len(feature_snapshot.get("contacts", {})),
            has_skip_trace=1 if feature_snapshot.get("skip_trace") else 0,
            activity_velocity=feature_snapshot.get("activity", {}).get("actions_last_7d"),
        )

        db.add(log)
        db.commit()

        logger.info(f"Logged prediction for property {property_id}: {predicted_probability}")
        return log

    # ── Private Methods ──

    async def _update_prediction_logs(
        self,
        db: Session,
        property_id: int,
        outcome: OutcomeStatus,
        days_to_close: int | None,
    ):
        """Back-fill prediction logs when outcome is known."""
        logs = (
            db.query(PredictionLog)
            .filter(
                PredictionLog.property_id == property_id,
                PredictionLog.actual_outcome.is_(None),
            )
            .all()
        )

        for log in logs:
            log.actual_outcome = outcome
            log.actual_days_to_close = days_to_close
            log.outcome_recorded_at = datetime.now(timezone.utc)

            # Calculate accuracy
            # For binary classification: >0.5 = predicted won
            predicted_won = log.predicted_probability > 0.5
            actual_won = outcome == OutcomeStatus.CLOSED_WON

            log.probability_error = log.predicted_probability - (1.0 if actual_won else 0.0)
            log.was_correct_direction = 1 if predicted_won == actual_won else 0

        db.commit()

    async def _update_agent_metrics(self, db: Session, agent_id: int):
        """Update agent performance metrics for current month."""
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Check if metrics already exist for this month
        existing = (
            db.query(AgentPerformanceMetrics)
            .filter(
                AgentPerformanceMetrics.agent_id == agent_id,
                AgentPerformanceMetrics.period_type == "month",
                AgentPerformanceMetrics.period_start == month_start,
            )
            .first()
        )

        if existing:
            metrics = existing
        else:
            metrics = AgentPerformanceMetrics(
                agent_id=agent_id,
                period_type="month",
                period_start=month_start,
                period_end=now,
            )
            db.add(metrics)

        # Calculate metrics
        completed_outcomes = (
            db.query(DealOutcome)
            .filter(
                DealOutcome.agent_id == agent_id,
                DealOutcome.closed_at >= month_start,
            )
            .all()
        )

        metrics.total_deals = len(completed_outcomes)
        metrics.closed_won = len([o for o in completed_outcomes if o.status == OutcomeStatus.CLOSED_WON])
        metrics.closing_rate = (
            metrics.closed_won / metrics.total_deals if metrics.total_deals > 0 else 0
        )

        metrics.total_volume = sum([o.final_sale_price or 0 for o in completed_outcomes])
        metrics.average_deal_size = (
            metrics.total_volume / metrics.total_deals if metrics.total_deals > 0 else 0
        )

        days_to_close = [o.days_to_close for o in completed_outcomes if o.days_to_close]
        metrics.average_days_to_close = (
            sum(days_to_close) / len(days_to_close) if days_to_close else None
        )

        db.commit()

    def _analyze_by_property_type(
        self, won_props: list[Property], lost_props: list[Property]
    ) -> dict[str, Any]:
        """Analyze win rate by property type."""
        type_counts = {}
        for p in won_props:
            t = p.property_type.value if p.property_type else "unknown"
            type_counts[t] = type_counts.get(t, 0) + 1

        lost_type_counts = {}
        for p in lost_props:
            t = p.property_type.value if p.property_type else "unknown"
            lost_type_counts[t] = lost_type_counts.get(t, 0) + 1

        # Calculate win rates
        win_rates = {}
        for t in set(list(type_counts.keys()) + list(lost_type_counts.keys())):
            won = type_counts.get(t, 0)
            total = won + lost_type_counts.get(t, 0)
            win_rates[t] = won / total if total > 0 else 0

        best = sorted(win_rates.items(), key=lambda x: x[1], reverse=True)[:3]
        worst = sorted(win_rates.items(), key=lambda x: x[1])[:3]

        return {
            "best": [{"type": t, "win_rate": f"{r*100:.0f}%"} for t, r in best],
            "worst": [{"type": t, "win_rate": f"{r*100:.0f}%"} for t, r in worst],
        }

    def _analyze_by_city(
        self, won_props: list[Property], lost_props: list[Property]
    ) -> dict[str, Any]:
        """Analyze win rate by city."""
        city_counts = {}
        for p in won_props:
            city_counts[p.city] = city_counts.get(p.city, 0) + 1

        lost_city_counts = {}
        for p in lost_props:
            lost_city_counts[p.city] = lost_city_counts.get(p.city, 0) + 1

        win_rates = {}
        all_cities = set(list(city_counts.keys()) + list(lost_city_counts.keys()))
        for c in all_cities:
            won = city_counts.get(c, 0)
            total = won + lost_city_counts.get(c, 0)
            if total >= 2:  # Only include cities with 2+ deals
                win_rates[c] = won / total if total > 0 else 0

        best = sorted(win_rates.items(), key=lambda x: x[1], reverse=True)[:3]
        worst = sorted(win_rates.items(), key=lambda x: x[1])[:3]

        return {
            "best": [{"city": c, "win_rate": f"{r*100:.0f}%"} for c, r in best],
            "worst": [{"city": c, "win_rate": f"{r*100:.0f}%"} for c, r in worst],
        }

    def _analyze_price_ranges(
        self, won_props: list[Property], lost_props: list[Property]
    ) -> dict[str, Any]:
        """Analyze win rate by price range."""
        # Define price buckets
        buckets = {
            "under_300k": (0, 300000),
            "300k_500k": (300000, 500000),
            "500k_750k": (500000, 750000),
            "750k_1m": (750000, 1000000),
            "over_1m": (1000000, float("inf")),
        }

        bucket_stats = {}
        for bucket, (min_p, max_p) in buckets.items():
            won = len([p for p in won_props if min_p <= p.price < max_p])
            lost = len([p for p in lost_props if min_p <= p.price < max_p])
            total = won + lost
            bucket_stats[bucket] = {
                "won": won,
                "lost": lost,
                "total": total,
                "win_rate": won / total if total > 0 else 0,
            }

        # Find optimal range
        optimal = max(
            [(k, v) for k, v in bucket_stats.items() if v["total"] >= 2],
            key=lambda x: x[1]["win_rate"],
            default=(None, None),
        )

        return {
            "optimal": {
                "range": optimal[0],
                "win_rate": f"{optimal[1]['win_rate']*100:.0f}%" if optimal[1] else None,
                "deals": optimal[1]["total"] if optimal[1] else 0,
            },
            "all_buckets": bucket_stats,
        }

    async def _analyze_prediction_factors(
        self, db: Session, won_ids: list[int], lost_ids: list[int]
    ) -> tuple[list[str], list[str]]:
        """Analyze which factors correlated with success/failure."""
        # Get average metrics for won vs lost
        won_logs = (
            db.query(PredictionLog)
            .filter(PredictionLog.property_id.in_(won_ids))
            .all()
        )
        lost_logs = (
            db.query(PredictionLog)
            .filter(PredictionLog.property_id.in_(lost_ids))
            .all()
        )

        success_factors = []
        avoid_factors = []

        if won_logs and lost_logs:
            # Compare deal scores
            avg_won_score = (
                sum([l.deal_score for l in won_logs if l.deal_score]) / len(won_logs)
                if won_logs
                else 0
            )
            avg_lost_score = (
                sum([l.deal_score for l in lost_logs if l.deal_score]) / len(lost_logs)
                if lost_logs
                else 0
            )

            if avg_won_score > avg_lost_score + 10:
                success_factors.append(f"Higher deal scores ({avg_won_score:.0f} vs {avg_lost_score:.0f})")
            elif avg_lost_score > avg_won_score + 10:
                avoid_factors.append(f"Low deal scores correlate with failures")

            # Compare completion rates
            avg_won_completion = (
                sum([l.completion_rate for l in won_logs if l.completion_rate]) / len(won_logs)
                if won_logs
                else 0
            )
            avg_lost_completion = (
                sum([l.completion_rate for l in lost_logs if l.completion_rate]) / len(lost_logs)
                if lost_logs
                else 0
            )

            if avg_won_completion > avg_lost_completion + 20:
                success_factors.append("Higher contract completion rates")

        return success_factors, avoid_factors

    def _get_period_start(self, period: str) -> datetime:
        """Get start date for period analysis."""
        now = datetime.now(timezone.utc)
        if period == "week":
            return now - timedelta(days=7)
        elif period == "month":
            return now - timedelta(days=30)
        elif period == "quarter":
            return now - timedelta(days=90)
        elif period == "year":
            return now - timedelta(days=365)
        return now - timedelta(days=30)

    def _build_pattern_voice_summary(
        self, type_stats: dict, city_stats: dict, price_analysis: dict
    ) -> str:
        """Build voice summary of agent patterns."""
        parts = []

        if type_stats.get("best"):
            best_type = type_stats["best"][0]
            parts.append(f"You perform best with {best_type['type']} properties")

        if city_stats.get("best"):
            best_city = city_stats["best"][0]
            parts.append(f"and in {best_city['city']}")

        if price_analysis.get("optimal", {}).get("range"):
            range_name = price_analysis["optimal"]["range"].replace("_", " ")
            win_rate = price_analysis["optimal"]["win_rate"]
            parts.append(f"with a {win_rate} win rate in the {range_name} range")

        return ". ".join(parts) + "." if parts else "Insufficient data for pattern analysis."

    def _build_accuracy_voice_summary(self, mae: float | None, directional_accuracy: float | None) -> str:
        """Build voice summary of prediction accuracy."""
        parts = []

        if mae is not None:
            if mae < 0.15:
                parts.append(f"Predictions are highly accurate (MAE: {mae:.2f})")
            elif mae < 0.25:
                parts.append(f"Predictions are moderately accurate (MAE: {mae:.2f})")
            else:
                parts.append(f"Predictions need improvement (MAE: {mae:.2f})")

        if directional_accuracy is not None:
            parts.append(f"Correctly predicted outcome direction {directional_accuracy:.0f}% of the time")

        return ". ".join(parts) if parts else "Insufficient data for accuracy assessment."


learning_system_service = LearningSystemService()
