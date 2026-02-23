"""Relationship Intelligence — track relationship health and predict best communication."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.contact import Contact
from app.models.property_note import PropertyNote, NoteSource
from app.models.conversation_history import ConversationHistory
from app.models.contract import Contract, ContractStatus
from app.models.offer import Offer, OfferStatus
from app.models.property import Property
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


# Simple sentiment analyzer (VADER-like without external dependency)
class SimpleSentimentAnalyzer:
    """Rule-based sentiment analysis for contact interactions."""

    # Positive words
    POSITIVE_WORDS = {
        "great", "excellent", "good", "love", "happy", "excited", "interested",
        "yes", "sure", "absolutely", "definitely", "agree", "sounds good",
        "perfect", "wonderful", "fantastic", "pleased", "thank", "thanks",
        "appreciate", "looking forward", "optimistic", "confident", "enthusiastic",
        "positive", "proceed", "moving forward", "let's do it", "on board",
    }

    # Negative words
    NEGATIVE_WORDS = {
        "bad", "terrible", "awful", "hate", "disappointed", "frustrated",
        "angry", "upset", "no", "not interested", "pass", "reject", "decline",
        "problem", "issue", "concern", "worried", "nervous", "skeptical",
        "doubt", "unfortunately", "can't", "won't", "unable", "difficult",
        "expensive", "too high", "think about it", "maybe later", "not sure",
        "negative", "concerned", "hesitant", "reluctant",
    }

    # Urgency words
    URGENCY_WORDS = {
        "urgent", "asap", "immediately", "right away", "soon", "quickly",
        "deadline", "time sensitive", "hurry", "rush", "waiting", "pending",
    }

    @classmethod
    def analyze_sentiment(cls, text: str) -> dict[str, Any]:
        """Analyze sentiment of text.

        Returns:
            {
                "sentiment": "positive" | "neutral" | "negative",
                "sentiment_score": -1.0 to 1.0,
                "has_urgency": bool,
                "emotional_tone": "enthusiastic" | "professional" | "concerned" | "urgent",
            }
        """
        if not text:
            return {
                "sentiment": "neutral",
                "sentiment_score": 0.0,
                "has_urgency": False,
                "emotional_tone": "neutral",
            }

        text_lower = text.lower()

        # Count positive and negative words
        positive_count = sum(1 for word in cls.POSITIVE_WORDS if word in text_lower)
        negative_count = sum(1 for word in cls.NEGATIVE_WORDS if word in text_lower)
        urgency_count = sum(1 for word in cls.URGENCY_WORDS if word in text_lower)

        # Calculate sentiment score (-1 to 1)
        total_words = positive_count + negative_count
        if total_words == 0:
            sentiment_score = 0.0
        else:
            sentiment_score = (positive_count - negative_count) / max(1, total_words)

        # Determine sentiment category
        if sentiment_score > 0.3:
            sentiment = "positive"
        elif sentiment_score < -0.3:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        # Check urgency
        has_urgency = urgency_count > 0

        # Determine emotional tone
        if has_urgency:
            emotional_tone = "urgent"
        elif sentiment_score > 0.6:
            emotional_tone = "enthusiastic"
        elif sentiment_score < -0.5:
            emotional_tone = "concerned"
        else:
            emotional_tone = "professional"

        return {
            "sentiment": sentiment,
            "sentiment_score": round(sentiment_score, 2),
            "has_urgency": has_urgency,
            "emotional_tone": emotional_tone,
            "positive_words": positive_count,
            "negative_words": negative_count,
            "urgency_words": urgency_count,
        }


class RelationshipIntelligenceService:
    """Track relationship health and predict optimal communication strategies."""

    def __init__(self):
        self.sentiment_analyzer = SimpleSentimentAnalyzer()

    async def score_relationship_health(
        self, db: Session, contact_id: int
    ) -> dict[str, Any]:
        """Track relationship strength based on interactions.

        Returns:
            {
                "health_score": 0-100,
                "trend": "improving" | "stable" | "declining",
                "communication_frequency": "high" | "medium" | "low",
                "responsiveness": "high" | "medium" | "low",
                "sentiment_trend": {...},
                "recommended_action": "...",
                "voice_summary": "..."
            }
        """
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            return {"error": f"Contact {contact_id} not found"}

        # Gather interaction data
        interactions = await self._gather_interactions(db, contact)

        # Calculate health components
        freq_score = self._calculate_communication_frequency(interactions)
        response_score = self._calculate_responsiveness(interactions)
        sentiment_data = self._analyze_sentiment_trend(interactions)
        engagement_score = self._calculate_engagement_depth(interactions)

        # Weighted overall score
        weights = {"frequency": 0.25, "responsiveness": 0.30, "sentiment": 0.25, "engagement": 0.20}
        health_score = (
            freq_score * weights["frequency"]
            + response_score * weights["responsiveness"]
            + sentiment_data["avg_sentiment_score"] * 100 * weights["sentiment"]
            + engagement_score * weights["engagement"]
        )

        # Determine trend
        trend = self._calculate_trend(interactions)

        # Build result
        result = {
            "contact_id": contact.id,
            "contact_name": contact.name,
            "property_id": contact.property_id,
            "health_score": round(health_score, 1),
            "trend": trend,
            "communication_frequency": self._categorize_frequency(freq_score),
            "responsiveness": self._categorize_responsiveness(response_score),
            "sentiment_trend": sentiment_data,
            "engagement_score": round(engagement_score, 1),
            "recommended_action": self._suggest_contact_action(health_score, trend, sentiment_data),
        }

        # Add voice summary
        result["voice_summary"] = self._build_health_voice_summary(result)

        return result

    async def predict_best_contact_method(
        self, db: Session, contact_id: int, message_type: str = "check_in"
    ) -> dict[str, Any]:
        """Predict: phone call, email, or text message?

        Analyzes historical response rates by method and message type.
        """
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            return {"error": f"Contact {contact_id} not found"}

        # Get interaction history
        interactions = await self._gather_interactions(db, contact)

        # Count successful interactions by method
        method_success = {
            "phone_call": {"attempts": 0, "responses": 0, "positive_sentiment": 0},
            "email": {"attempts": 0, "responses": 0, "positive_sentiment": 0},
            "text": {"attempts": 0, "responses": 0, "positive_sentiment": 0},
        }

        for interaction in interactions:
            method = interaction.get("method")
            if method in method_success:
                method_success[method]["attempts"] += 1
                if interaction.get("had_response"):
                    method_success[method]["responses"] += 1
                if interaction.get("sentiment") == "positive":
                    method_success[method]["positive_sentiment"] += 1

        # Calculate success rates
        predictions = {}
        for method, stats in method_success.items():
            if stats["attempts"] > 0:
                response_rate = stats["responses"] / stats["attempts"]
                positive_rate = (
                    stats["positive_sentiment"] / max(1, stats["responses"])
                )
                success_score = response_rate * 0.6 + positive_rate * 0.4
                predictions[method] = {
                    "success_rate": round(response_rate * 100, 1),
                    "positive_response_rate": round(positive_rate * 100, 1),
                    "success_score": round(success_score, 2),
                    "attempts": stats["attempts"],
                }

        # Determine best method
        if predictions:
            best_method = max(predictions.items(), key=lambda x: x[1]["success_score"])
        else:
            # No data - default based on contact info
            if contact.phone:
                best_method = ("phone_call", {"success_rate": 50, "attempts": 0})
            elif contact.email:
                best_method = ("email", {"success_rate": 50, "attempts": 0})
            else:
                best_method = ("email", {"success_rate": 30, "attempts": 0})  # Fallback

        return {
            "contact_id": contact.id,
            "contact_name": contact.name,
            "message_type": message_type,
            "recommended_method": best_method[0],
            "method_predictions": predictions,
            "reasoning": self._explain_method_choice(best_method, predictions),
            "voice_summary": f"For {contact.name}, I recommend {best_method[0]} - {self._explain_method_choice(best_method, predictions)}",
        }

    async def analyze_contact_sentiment(
        self, db: Session, contact_id: int, days: int = 30
    ) -> dict[str, Any]:
        """Analyze sentiment trend for a contact over time.

        Useful for:
        - Detecting cooling relationships
        - Measuring campaign effectiveness
        - Identifying upset contacts
        """
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            return {"error": f"Contact {contact_id} not found"}

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Get notes and conversation history
        notes = (
            db.query(PropertyNote)
            .filter(
                PropertyNote.property_id == contact.property_id,
                PropertyNote.created_at >= cutoff,
            )
            .all()
        )

        # Filter notes related to this contact
        contact_notes = [
            n
            for n in notes
            if contact.name.lower() in n.content.lower()
            or (contact.email and contact.email.lower() in n.content.lower())
        ]

        # Analyze each note
        sentiment_history = []
        for note in contact_notes:
            sentiment = self.sentiment_analyzer.analyze_sentiment(note.content)
            sentiment_history.append({
                "date": note.created_at.isoformat(),
                "source": note.source.value if note.source else "unknown",
                "sentiment": sentiment["sentiment"],
                "sentiment_score": sentiment["sentiment_score"],
                "has_urgency": sentiment["has_urgency"],
                "emotional_tone": sentiment["emotional_tone"],
                "excerpt": note.content[:200] if note.content else "",
            })

        # Calculate overall trend
        if sentiment_history:
            avg_score = sum([s["sentiment_score"] for s in sentiment_history]) / len(
                sentiment_history
            )
            recent_score = sentiment_history[0]["sentiment_score"] if sentiment_history else 0

            if recent_score > avg_score + 0.2:
                trend = "improving"
            elif recent_score < avg_score - 0.2:
                trend = "declining"
            else:
                trend = "stable"
        else:
            avg_score = 0
            trend = "insufficient_data"

        return {
            "contact_id": contact.id,
            "contact_name": contact.name,
            "period_days": days,
            "total_interactions": len(sentiment_history),
            "average_sentiment": round(avg_score, 2),
            "recent_sentiment": sentiment_history[0]["sentiment_score"] if sentiment_history else 0,
            "trend": trend,
            "sentiment_history": sentiment_history,
            "voice_summary": self._build_sentiment_voice_summary(contact.name, trend, avg_score, len(sentiment_history)),
        }

    # ── Private Methods ──

    async def _gather_interactions(
        self, db: Session, contact: Contact
    ) -> list[dict[str, Any]]:
        """Gather all interactions for a contact."""
        interactions = []
        cutoff_30d = datetime.now(timezone.utc) - timedelta(days=30)

        # Get notes related to this contact
        notes = (
            db.query(PropertyNote)
            .filter(PropertyNote.property_id == contact.property_id)
            .filter(PropertyNote.created_at >= cutoff_30d)
            .all()
        )

        for note in notes:
            if contact.name.lower() in note.content.lower():
                sentiment = self.sentiment_analyzer.analyze_sentiment(note.content)
                interactions.append({
                    "date": note.created_at,
                    "type": "note",
                    "source": note.source.value if note.source else "manual",
                    "content": note.content,
                    "sentiment": sentiment["sentiment"],
                    "sentiment_score": sentiment["sentiment_score"],
                    "method": self._infer_method_from_note(note),
                })

        # Get contracts involving this contact
        if contact.role:
            contracts = (
                db.query(Contract)
                .filter(
                    Contract.property_id == contact.property_id,
                    Contract.contact_id == contact.id,
                )
                .all()
            )

            for contract in contracts:
                interactions.append({
                    "date": contract.created_at,
                    "type": "contract",
                    "status": contract.status.value,
                    "method": "email",  # Contracts typically sent via email
                    "had_response": contract.status in [ContractStatus.IN_PROGRESS, ContractStatus.COMPLETED],
                })

        # Sort by date
        interactions.sort(key=lambda x: x["date"], reverse=True)
        return interactions

    def _infer_method_from_note(self, note: PropertyNote) -> str:
        """Infer communication method from note content."""
        content_lower = note.content.lower()

        if note.source == NoteSource.PHONE_CALL:
            return "phone_call"
        elif note.source == NoteSource.VOICE:
            return "phone_call"
        elif "call" in content_lower or "called" in content_lower or "spoke" in content_lower:
            return "phone_call"
        elif "text" in content_lower or "message" in content_lower:
            return "text"
        else:
            return "email"

    def _calculate_communication_frequency(self, interactions: list[dict]) -> float:
        """Calculate communication frequency score (0-100)."""
        if not interactions:
            return 0.0

        # Count interactions in last 30 days
        count = len(interactions)

        # Score: 10+ = 100, 5 = 50, 0 = 0
        return max(0.0, min(100.0, count * 10))

    def _calculate_responsiveness(self, interactions: list[dict]) -> float:
        """Calculate responsiveness score (0-100)."""
        if not interactions:
            return 0.0

        # Count interactions with responses
        responses = [i for i in interactions if i.get("had_response")]
        response_rate = len(responses) / len(interactions) if interactions else 0

        return response_rate * 100

    def _calculate_engagement_depth(self, interactions: list[dict]) -> float:
        """Calculate engagement depth score (0-100).

        Based on variety of interaction types and sentiment quality.
        """
        if not interactions:
            return 0.0

        # Variety bonus (different types of interactions)
        types = set([i.get("type") for i in interactions])
        variety_score = min(50.0, len(types) * 15)

        # Sentiment quality
        positive_count = len([i for i in interactions if i.get("sentiment") == "positive"])
        sentiment_score = min(50.0, positive_count * 10)

        return variety_score + sentiment_score

    def _analyze_sentiment_trend(self, interactions: list[dict]) -> dict[str, Any]:
        """Analyze sentiment trend over time."""
        sentiment_scores = [i.get("sentiment_score", 0) for i in interactions if "sentiment_score" in i]

        if not sentiment_scores:
            return {
                "avg_sentiment_score": 0,
                "recent_score": 0,
                "trend": "no_data",
            }

        avg_score = sum(sentiment_scores) / len(sentiment_scores)
        recent_score = sentiment_scores[0] if sentiment_scores else 0

        if recent_score > avg_score + 0.2:
            trend = "improving"
        elif recent_score < avg_score - 0.2:
            trend = "declining"
        else:
            trend = "stable"

        return {
            "avg_sentiment_score": avg_score,
            "recent_score": recent_score,
            "trend": trend,
        }

    def _calculate_trend(self, interactions: list[dict]) -> str:
        """Calculate overall relationship trend."""
        if not interactions:
            return "unknown"

        # Compare recent (last 7 days) to previous (7-30 days ago)
        cutoff_7d = datetime.now(timezone.utc) - timedelta(days=7)
        cutoff_30d = datetime.now(timezone.utc) - timedelta(days=30)

        recent_count = len([i for i in interactions if i["date"] >= cutoff_7d])
        older_count = len([i for i in interactions if cutoff_30d <= i["date"] < cutoff_7d])

        if recent_count > older_count * 1.5:
            return "improving"
        elif recent_count < older_count * 0.5:
            return "declining"
        else:
            return "stable"

    def _categorize_frequency(self, score: float) -> str:
        """Categorize communication frequency."""
        if score >= 70:
            return "high"
        elif score >= 40:
            return "medium"
        else:
            return "low"

    def _categorize_responsiveness(self, score: float) -> str:
        """Categorize responsiveness."""
        if score >= 70:
            return "high"
        elif score >= 40:
            return "medium"
        else:
            return "low"

    def _suggest_contact_action(
        self, health_score: float, trend: str, sentiment_data: dict
    ) -> str:
        """Suggest next action based on relationship health."""
        if health_score < 40:
            return "rebuild_relationship"
        elif health_score < 60:
            return "check_in"
        elif trend == "declining":
            return "re_engage"
        elif sentiment_data.get("recent_score", 0) < -0.3:
            return "address_concerns"
        elif health_score >= 80:
            return "maintain"
        else:
            return "continue_normally"

    def _explain_method_choice(
        self, best_method: tuple, predictions: dict
    ) -> str:
        """Explain why a contact method is recommended."""
        method, stats = best_method

        if stats.get("attempts", 0) == 0:
            return f"no historical data - {method} is the default option"

        success_rate = stats.get("success_rate", 0)
        return f"{success_rate}% success rate based on past interactions"

    def _build_health_voice_summary(self, result: dict) -> str:
        """Build voice summary for relationship health."""
        name = result["contact_name"]
        score = result["health_score"]
        trend = result["trend"]
        freq = result["communication_frequency"]
        response = result["responsiveness"]

        return (
            f"{name}'s relationship health is {score:.0f}/100, {trend}. "
            f"{freq.capitalize()} communication frequency, {response} responsiveness. "
            f"Recommended: {result['recommended_action'].replace('_', ' ')}."
        )

    def _build_sentiment_voice_summary(
        self, name: str, trend: str, avg_score: float, count: int
    ) -> str:
        """Build voice summary for sentiment analysis."""
        if trend == "insufficient_data":
            return f"Not enough interactions to analyze sentiment for {name}."

        sentiment_label = "positive" if avg_score > 0.2 else "negative" if avg_score < -0.2 else "neutral"

        return (
            f"{name} shows {sentiment_label} sentiment (score: {avg_score:.1f}) "
            f"across {count} interactions, trend: {trend}."
        )


relationship_intelligence_service = RelationshipIntelligenceService()
