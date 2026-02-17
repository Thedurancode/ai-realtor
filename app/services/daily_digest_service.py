"""Daily digest service — AI-generated morning briefing."""

import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationType, NotificationPriority
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class DailyDigestService:
    """Generate AI-powered daily briefings from insights + analytics + notifications."""

    async def generate_digest(self, db: Session) -> dict:
        """Gather data and generate AI briefing."""
        data = self._gather_data(db)
        digest = await self._generate_ai_digest(data)
        self._save_as_notification(db, digest)
        return digest

    def _gather_data(self, db: Session) -> dict:
        """Collect insights, analytics, and recent notifications."""
        from app.services.insights_service import insights_service
        from app.services.analytics_service import analytics_service

        insights = insights_service.get_insights(db)
        portfolio = analytics_service.get_portfolio_summary(db)

        # Recent notifications (last 24h)
        from sqlalchemy import desc
        recent_notifs = (
            db.query(Notification)
            .filter(Notification.type != NotificationType.DAILY_DIGEST)
            .order_by(desc(Notification.created_at))
            .limit(20)
            .all()
        )

        notif_list = []
        for n in recent_notifs:
            notif_list.append({
                "type": n.type.value if hasattr(n.type, 'value') else str(n.type),
                "title": n.title,
                "message": n.message,
                "priority": n.priority.value if hasattr(n.priority, 'value') else str(n.priority),
                "property_id": n.property_id,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            })

        return {
            "insights": insights,
            "portfolio": portfolio,
            "recent_notifications": notif_list,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _generate_ai_digest(self, data: dict) -> dict:
        """Use Claude to generate a natural daily briefing."""
        prompt = f"""You are a real estate AI assistant generating a daily morning briefing.

Based on the following data, write a concise daily digest with two sections:

1. **Full Briefing** (3-5 paragraphs): Cover portfolio snapshot, urgent alerts, contract status, activity summary, and top recommendations.
2. **Voice Summary** (2-3 sentences, under 60 words): A quick spoken summary for text-to-speech.

Also extract:
- key_highlights (list of 3-5 one-line highlights)
- urgent_actions (list of actions needing immediate attention)

DATA:
{json.dumps(data, default=str, indent=2)}

Respond in JSON format:
{{
  "digest_text": "...",
  "voice_summary": "...",
  "key_highlights": ["...", "..."],
  "urgent_actions": ["...", "..."]
}}"""

        try:
            text = llm_service.generate(
                prompt, model="claude-sonnet-4-5-20250514", max_tokens=1500
            ).strip()
            # Strip markdown code fences if present
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

            result = json.loads(text)
            result["generated_at"] = datetime.now(timezone.utc).isoformat()
            return result
        except Exception as e:
            logger.error("AI digest generation failed: %s", e)
            # Fallback to data-driven summary
            insights = data.get("insights", {})
            portfolio = data.get("portfolio", {})
            pipeline = portfolio.get("pipeline", {})
            total_alerts = insights.get("total_alerts", 0)
            total_props = pipeline.get("total", 0)

            return {
                "digest_text": (
                    f"Daily digest: {total_props} properties in portfolio with "
                    f"{total_alerts} alert(s). "
                    f"{insights.get('voice_summary', 'No alerts.')} "
                    f"{portfolio.get('voice_summary', '')}"
                ),
                "voice_summary": insights.get("voice_summary", "No updates today."),
                "key_highlights": [f"{total_alerts} alerts", f"{total_props} properties"],
                "urgent_actions": [a["message"] for a in insights.get("urgent", [])],
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

    def _save_as_notification(self, db: Session, digest: dict):
        """Store digest as a notification for retrieval."""
        notif = Notification(
            type=NotificationType.DAILY_DIGEST,
            priority=NotificationPriority.LOW,
            title="Daily Digest",
            message=digest.get("voice_summary", "Your daily briefing is ready."),
            data=json.dumps(digest, default=str),
            icon="\U0001f4cb",
            auto_dismiss_seconds=None,
        )
        db.add(notif)
        db.commit()
        logger.info("Daily digest saved as notification #%d", notif.id)

    def get_latest_digest(self, db: Session) -> dict | None:
        """Get the most recent daily digest."""
        from sqlalchemy import desc
        notif = (
            db.query(Notification)
            .filter(Notification.type == NotificationType.DAILY_DIGEST)
            .order_by(desc(Notification.created_at))
            .first()
        )
        if not notif or not notif.data:
            return None
        try:
            digest = json.loads(notif.data)
            digest["notification_id"] = notif.id
            digest["created_at"] = notif.created_at.isoformat() if notif.created_at else None
            return digest
        except Exception:
            return None

    def get_digest_history(self, db: Session, days: int = 7) -> list[dict]:
        """Get past digests."""
        from datetime import timedelta
        from sqlalchemy import desc

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        notifs = (
            db.query(Notification)
            .filter(
                Notification.type == NotificationType.DAILY_DIGEST,
                Notification.created_at >= cutoff,
            )
            .order_by(desc(Notification.created_at))
            .all()
        )

        results = []
        for n in notifs:
            try:
                digest = json.loads(n.data) if n.data else {}
                digest["notification_id"] = n.id
                digest["created_at"] = n.created_at.isoformat() if n.created_at else None
                results.append(digest)
            except Exception:
                continue
        return results


daily_digest_service = DailyDigestService()
