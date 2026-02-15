"""Activity Timeline service — unified chronological event feed."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.conversation_history import ConversationHistory
from app.models.notification import Notification
from app.models.property_note import PropertyNote
from app.models.scheduled_task import ScheduledTask
from app.models.contract import Contract
from app.models.zillow_enrichment import ZillowEnrichment
from app.models.skip_trace import SkipTrace

ALL_EVENT_TYPES = frozenset(
    ["conversation", "notification", "note", "task", "contract", "enrichment", "skip_trace"]
)


class ActivityTimelineService:
    """Aggregates activity across data sources into a unified timeline."""

    def get_timeline(
        self,
        db: Session,
        property_id: int | None = None,
        event_types: list[str] | None = None,
        search: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        types_to_fetch = set(event_types) & ALL_EVENT_TYPES if event_types else ALL_EVENT_TYPES
        events: list[dict] = []

        fetchers = {
            "conversation": self._get_conversation_events,
            "notification": self._get_notification_events,
            "note": self._get_note_events,
            "task": self._get_task_events,
            "contract": self._get_contract_events,
            "enrichment": self._get_enrichment_events,
            "skip_trace": self._get_skip_trace_events,
        }

        for etype in types_to_fetch:
            fn = fetchers.get(etype)
            if fn:
                events.extend(fn(db, property_id, search, start_date, end_date))

        # Sort by timestamp descending (normalize tz-aware vs naive)
        from datetime import timezone as _tz
        def _sort_key(ev: dict) -> datetime:
            ts = ev["timestamp"]
            if ts is None:
                return datetime.min.replace(tzinfo=_tz.utc)
            if ts.tzinfo is None:
                return ts.replace(tzinfo=_tz.utc)
            return ts

        events.sort(key=_sort_key, reverse=True)
        total_events = len(events)
        page = events[offset : offset + limit]

        # Serialize timestamps for JSON
        for ev in page:
            ts = ev["timestamp"]
            if isinstance(ts, datetime):
                ev["timestamp"] = ts.isoformat()

        return {
            "total_events": total_events,
            "limit": limit,
            "offset": offset,
            "property_id": property_id,
            "events": page,
            "voice_summary": self._build_voice_summary(page, total_events, property_id),
        }

    # ── Event fetchers ──

    def _get_conversation_events(
        self, db: Session, property_id: int | None, search: str | None,
        start_date: datetime | None, end_date: datetime | None,
    ) -> list[dict]:
        query = db.query(ConversationHistory)
        if property_id is not None:
            query = query.filter(ConversationHistory.property_id == property_id)
        if search:
            query = query.filter(or_(
                ConversationHistory.tool_name.ilike(f"%{search}%"),
                ConversationHistory.input_summary.ilike(f"%{search}%"),
                ConversationHistory.output_summary.ilike(f"%{search}%"),
            ))
        if start_date:
            query = query.filter(ConversationHistory.created_at >= start_date)
        if end_date:
            query = query.filter(ConversationHistory.created_at <= end_date)

        results: list[dict] = []
        for item in query.all():
            results.append({
                "event_type": "conversation",
                "timestamp": item.created_at,
                "property_id": item.property_id,
                "title": f"Tool: {item.tool_name}",
                "description": item.output_summary or item.input_summary or "Tool executed",
                "metadata": {
                    "tool_name": item.tool_name,
                    "success": bool(item.success),
                    "duration_ms": item.duration_ms,
                    "session_id": item.session_id,
                },
            })
        return results

    def _get_notification_events(
        self, db: Session, property_id: int | None, search: str | None,
        start_date: datetime | None, end_date: datetime | None,
    ) -> list[dict]:
        query = db.query(Notification)
        if property_id is not None:
            query = query.filter(Notification.property_id == property_id)
        if search:
            query = query.filter(or_(
                Notification.title.ilike(f"%{search}%"),
                Notification.message.ilike(f"%{search}%"),
            ))
        if start_date:
            query = query.filter(Notification.created_at >= start_date)
        if end_date:
            query = query.filter(Notification.created_at <= end_date)

        results: list[dict] = []
        for item in query.all():
            results.append({
                "event_type": "notification",
                "timestamp": item.created_at,
                "property_id": item.property_id,
                "title": item.title,
                "description": item.message or "",
                "metadata": {
                    "notification_type": item.type.value,
                    "priority": item.priority.value,
                    "is_read": item.is_read,
                },
            })
        return results

    def _get_note_events(
        self, db: Session, property_id: int | None, search: str | None,
        start_date: datetime | None, end_date: datetime | None,
    ) -> list[dict]:
        query = db.query(PropertyNote)
        if property_id is not None:
            query = query.filter(PropertyNote.property_id == property_id)
        if search:
            query = query.filter(PropertyNote.content.ilike(f"%{search}%"))
        if start_date:
            query = query.filter(PropertyNote.created_at >= start_date)
        if end_date:
            query = query.filter(PropertyNote.created_at <= end_date)

        results: list[dict] = []
        for item in query.all():
            preview = item.content[:120] + "..." if len(item.content) > 120 else item.content
            results.append({
                "event_type": "note",
                "timestamp": item.created_at,
                "property_id": item.property_id,
                "title": f"Note ({item.source.value})",
                "description": preview,
                "metadata": {"source": item.source.value, "created_by": item.created_by},
            })
        return results

    def _get_task_events(
        self, db: Session, property_id: int | None, search: str | None,
        start_date: datetime | None, end_date: datetime | None,
    ) -> list[dict]:
        query = db.query(ScheduledTask)
        if property_id is not None:
            query = query.filter(ScheduledTask.property_id == property_id)
        if search:
            query = query.filter(or_(
                ScheduledTask.title.ilike(f"%{search}%"),
                ScheduledTask.description.ilike(f"%{search}%"),
            ))
        if start_date:
            query = query.filter(ScheduledTask.created_at >= start_date)
        if end_date:
            query = query.filter(ScheduledTask.created_at <= end_date)

        results: list[dict] = []
        for item in query.all():
            results.append({
                "event_type": "task",
                "timestamp": item.created_at,
                "property_id": item.property_id,
                "title": f"Task: {item.title}",
                "description": item.description or f"{item.task_type.value} scheduled",
                "metadata": {
                    "task_type": item.task_type.value,
                    "status": item.status.value,
                    "scheduled_at": item.scheduled_at.isoformat() if item.scheduled_at else None,
                },
            })
        return results

    def _get_contract_events(
        self, db: Session, property_id: int | None, search: str | None,
        start_date: datetime | None, end_date: datetime | None,
    ) -> list[dict]:
        query = db.query(Contract)
        if property_id is not None:
            query = query.filter(Contract.property_id == property_id)
        if search:
            query = query.filter(or_(
                Contract.name.ilike(f"%{search}%"),
                Contract.description.ilike(f"%{search}%"),
            ))

        results: list[dict] = []
        for c in query.all():
            base_meta = {"contract_id": c.id, "contract_name": c.name, "status": c.status.value, "is_required": c.is_required}

            # Created event
            if c.created_at and self._in_range(c.created_at, start_date, end_date):
                results.append({
                    "event_type": "contract",
                    "timestamp": c.created_at,
                    "property_id": c.property_id,
                    "title": f"Contract created: {c.name}",
                    "description": f"Status: {c.status.value}",
                    "metadata": {**base_meta, "action": "created"},
                })

            # Sent event
            if c.sent_at and self._in_range(c.sent_at, start_date, end_date):
                results.append({
                    "event_type": "contract",
                    "timestamp": c.sent_at,
                    "property_id": c.property_id,
                    "title": f"Contract sent: {c.name}",
                    "description": "Sent for signature",
                    "metadata": {**base_meta, "action": "sent"},
                })

            # Completed event
            if c.completed_at and self._in_range(c.completed_at, start_date, end_date):
                results.append({
                    "event_type": "contract",
                    "timestamp": c.completed_at,
                    "property_id": c.property_id,
                    "title": f"Contract completed: {c.name}",
                    "description": "All parties signed",
                    "metadata": {**base_meta, "action": "completed"},
                })

        return results

    def _get_enrichment_events(
        self, db: Session, property_id: int | None, search: str | None,
        start_date: datetime | None, end_date: datetime | None,
    ) -> list[dict]:
        query = db.query(ZillowEnrichment)
        if property_id is not None:
            query = query.filter(ZillowEnrichment.property_id == property_id)
        if start_date:
            query = query.filter(ZillowEnrichment.created_at >= start_date)
        if end_date:
            query = query.filter(ZillowEnrichment.created_at <= end_date)

        results: list[dict] = []
        for item in query.all():
            z_str = f"${item.zestimate:,.0f}" if item.zestimate else "N/A"
            results.append({
                "event_type": "enrichment",
                "timestamp": item.created_at,
                "property_id": item.property_id,
                "title": "Zillow enrichment",
                "description": f"Zestimate: {z_str}",
                "metadata": {"zestimate": item.zestimate, "rent_zestimate": item.rent_zestimate, "zpid": item.zpid},
            })
        return results

    def _get_skip_trace_events(
        self, db: Session, property_id: int | None, search: str | None,
        start_date: datetime | None, end_date: datetime | None,
    ) -> list[dict]:
        query = db.query(SkipTrace)
        if property_id is not None:
            query = query.filter(SkipTrace.property_id == property_id)
        if search:
            query = query.filter(SkipTrace.owner_name.ilike(f"%{search}%"))
        if start_date:
            query = query.filter(SkipTrace.created_at >= start_date)
        if end_date:
            query = query.filter(SkipTrace.created_at <= end_date)

        results: list[dict] = []
        for item in query.all():
            owner = item.owner_name or "Unknown"
            phone_count = len(item.phone_numbers) if item.phone_numbers else 0
            results.append({
                "event_type": "skip_trace",
                "timestamp": item.created_at,
                "property_id": item.property_id,
                "title": "Skip trace completed",
                "description": f"Owner: {owner}, {phone_count} phone(s)",
                "metadata": {
                    "owner_name": item.owner_name,
                    "phone_count": phone_count,
                    "email_count": len(item.emails) if item.emails else 0,
                },
            })
        return results

    # ── Helpers ──

    @staticmethod
    def _in_range(ts: datetime | None, start: datetime | None, end: datetime | None) -> bool:
        if ts is None:
            return False
        if start and ts < start:
            return False
        if end and ts > end:
            return False
        return True

    @staticmethod
    def _build_voice_summary(events: list[dict], total_events: int, property_id: int | None) -> str:
        if not events:
            scope = f"for property {property_id}" if property_id else "across your portfolio"
            return f"No activity found {scope}."

        scope = f"for property {property_id}" if property_id else "across your portfolio"
        parts = [f"{total_events} events {scope}."]

        # Count by type
        type_counts: dict[str, int] = {}
        for ev in events:
            t = ev["event_type"]
            type_counts[t] = type_counts.get(t, 0) + 1

        top = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        labels = {"conversation": "tool calls", "notification": "notifications", "note": "notes",
                  "task": "tasks", "contract": "contract events", "enrichment": "enrichments",
                  "skip_trace": "skip traces"}
        top_parts = [f"{cnt} {labels.get(et, et)}" for et, cnt in top]
        parts.append(f"Top types: {', '.join(top_parts)}.")

        most_recent = events[0]
        parts.append(f"Latest: {most_recent['title']}.")

        return " ".join(parts)


activity_timeline_service = ActivityTimelineService()
