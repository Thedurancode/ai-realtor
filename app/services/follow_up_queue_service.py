"""Smart Follow-Up Queue — AI-prioritized queue of properties needing attention."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.contact import Contact, ContactRole
from app.models.contract import Contract, ContractStatus
from app.models.conversation_history import ConversationHistory
from app.models.property import Property, PropertyStatus
from app.models.scheduled_task import ScheduledTask, TaskType, TaskStatus
from app.models.skip_trace import SkipTrace


class FollowUpQueueService:
    """Dynamically compute a ranked follow-up queue from existing data."""

    STALE_RECENT_HOURS = 24
    MAX_BASE_SCORE = 300
    DEADLINE_WARN_DAYS = 3
    UNSIGNED_STALE_DAYS = 3

    GRADE_MULTIPLIERS = {"A": 2.0, "B": 1.5, "C": 1.0, "D": 0.8, "F": 0.5}
    SCORE_THRESHOLDS = {"urgent": 100, "high": 60, "medium": 30}

    BONUS_DEADLINE = 40
    BONUS_OVERDUE_TASK = 35
    BONUS_UNSIGNED_CONTRACT = 30
    BONUS_SKIP_NO_OUTREACH = 25
    BONUS_MISSING_CONTACTS = 15

    CALL_TOOL_NAMES = frozenset({
        "make_property_phone_call",
        "call_property_owner_skip_trace",
        "call_contact_about_contract",
        "elevenlabs_call",
    })

    # ── Public API ──

    def get_queue(self, db: Session, limit: int = 10, priority: Optional[str] = None) -> dict:
        now = datetime.now(timezone.utc)
        recent_cutoff = now - timedelta(hours=self.STALE_RECENT_HOURS)

        # 1. Load candidate properties
        properties = self._get_candidate_properties(db)
        if not properties:
            return {"items": [], "total": 0, "voice_summary": "No follow-ups needed right now."}

        prop_ids = [p.id for p in properties]

        # 2. Batch-load all signals
        last_activities = self._get_last_activities(db, prop_ids)
        snoozed_ids = self._get_snoozed_ids(db, now)
        unsigned_contracts = self._get_unsigned_contracts(db, prop_ids)
        deadline_contracts = self._get_deadline_contracts(db, prop_ids, now)
        skip_no_outreach = self._get_skip_trace_no_outreach(db, prop_ids)
        overdue_tasks = self._get_overdue_tasks(db, prop_ids, now)
        missing_contacts = self._get_missing_contacts(db, prop_ids)

        # 3. Score each property
        scored = []
        for prop in properties:
            item = self._score_property(
                prop, now, recent_cutoff, last_activities, snoozed_ids,
                unsigned_contracts, deadline_contracts, skip_no_outreach,
                overdue_tasks, missing_contacts,
            )
            if item is not None:
                scored.append(item)

        # 4. Sort by score descending
        scored.sort(key=lambda x: x["score"], reverse=True)

        # 5. Filter by priority
        if priority:
            scored = [s for s in scored if s["priority"] == priority]

        total = len(scored)
        items = scored[:limit]

        # Add rank
        for i, item in enumerate(items, 1):
            item["rank"] = i

        voice_summary = self._build_voice_summary(items, total)
        return {"items": items, "total": total, "voice_summary": voice_summary}

    def complete_follow_up(self, db: Session, property_id: int, note: Optional[str] = None) -> dict:
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            return {"error": f"Property {property_id} not found"}

        entry = ConversationHistory(
            session_id="follow_up_queue",
            property_id=property_id,
            tool_name="complete_follow_up",
            input_summary=f"Follow-up completed for property #{property_id}" + (f": {note}" if note else ""),
            output_summary="Follow-up marked as done",
            success=1,
        )
        db.add(entry)

        if note:
            from app.models.property_note import PropertyNote, NoteSource
            db_note = PropertyNote(
                property_id=property_id,
                content=note,
                source=NoteSource.VOICE,
                created_by="follow_up_queue",
            )
            db.add(db_note)

        db.commit()
        return {"status": "completed", "property_id": property_id, "address": prop.address}

    def snooze_follow_up(self, db: Session, property_id: int, hours: int = 72) -> dict:
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            return {"error": f"Property {property_id} not found"}

        now = datetime.now(timezone.utc)
        snooze_until = now + timedelta(hours=hours)

        # Cancel any existing snooze for this property
        existing = (
            db.query(ScheduledTask)
            .filter(
                ScheduledTask.property_id == property_id,
                ScheduledTask.action == "snooze_follow_up",
                ScheduledTask.status == TaskStatus.PENDING,
            )
            .all()
        )
        for t in existing:
            t.status = TaskStatus.CANCELLED

        task = ScheduledTask(
            task_type=TaskType.FOLLOW_UP,
            status=TaskStatus.PENDING,
            title=f"Snooze follow-up: {prop.address}",
            description=f"Property #{property_id} snoozed until {snooze_until.isoformat()}",
            scheduled_at=snooze_until,
            property_id=property_id,
            action="snooze_follow_up",
            created_by="follow_up_queue",
        )
        db.add(task)
        db.commit()

        days = hours / 24
        label = f"{hours}h" if hours < 24 else f"{days:.0f} day{'s' if days != 1 else ''}"
        return {
            "status": "snoozed",
            "property_id": property_id,
            "address": prop.address,
            "snooze_until": snooze_until.isoformat(),
            "label": label,
        }

    # ── Candidate loading ──

    def _get_candidate_properties(self, db: Session) -> list[Property]:
        return (
            db.query(Property)
            .filter(Property.status != PropertyStatus.COMPLETE)
            .all()
        )

    # ── Batch signal queries ──

    def _get_last_activities(self, db: Session, prop_ids: list[int]) -> dict[int, datetime]:
        rows = (
            db.query(
                ConversationHistory.property_id,
                func.max(ConversationHistory.created_at).label("last_at"),
            )
            .filter(ConversationHistory.property_id.in_(prop_ids))
            .group_by(ConversationHistory.property_id)
            .all()
        )
        return {r.property_id: r.last_at for r in rows}

    def _get_snoozed_ids(self, db: Session, now: datetime) -> set[int]:
        rows = (
            db.query(ScheduledTask.property_id)
            .filter(
                ScheduledTask.action == "snooze_follow_up",
                ScheduledTask.status == TaskStatus.PENDING,
                ScheduledTask.scheduled_at > now,
                ScheduledTask.property_id.isnot(None),
            )
            .all()
        )
        return {r.property_id for r in rows}

    def _get_unsigned_contracts(self, db: Session, prop_ids: list[int]) -> dict[int, list[str]]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.UNSIGNED_STALE_DAYS)
        rows = (
            db.query(Contract.property_id, Contract.name)
            .filter(
                Contract.property_id.in_(prop_ids),
                Contract.is_required.is_(True),
                Contract.status.in_([ContractStatus.DRAFT, ContractStatus.SENT]),
                Contract.created_at < cutoff,
            )
            .all()
        )
        result: dict[int, list[str]] = {}
        for r in rows:
            result.setdefault(r.property_id, []).append(r.name)
        return result

    def _get_deadline_contracts(self, db: Session, prop_ids: list[int], now: datetime) -> dict[int, list[tuple[str, int]]]:
        warn_cutoff = now + timedelta(days=self.DEADLINE_WARN_DAYS)
        rows = (
            db.query(Contract.property_id, Contract.name, Contract.required_by_date)
            .filter(
                Contract.property_id.in_(prop_ids),
                Contract.is_required.is_(True),
                Contract.required_by_date.isnot(None),
                Contract.required_by_date <= warn_cutoff,
                Contract.status.notin_([ContractStatus.COMPLETED, ContractStatus.CANCELLED]),
            )
            .all()
        )
        result: dict[int, list[tuple[str, int]]] = {}
        for r in rows:
            deadline = r.required_by_date
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
            days_left = (deadline - now).days
            result.setdefault(r.property_id, []).append((r.name, days_left))
        return result

    def _get_skip_trace_no_outreach(self, db: Session, prop_ids: list[int]) -> set[int]:
        skip_traces = (
            db.query(SkipTrace.property_id, SkipTrace.created_at)
            .filter(SkipTrace.property_id.in_(prop_ids))
            .all()
        )
        if not skip_traces:
            return set()

        st_map = {r.property_id: r.created_at for r in skip_traces}

        # Check for phone calls after skip trace
        call_props = set()
        if st_map:
            calls = (
                db.query(ConversationHistory.property_id)
                .filter(
                    ConversationHistory.property_id.in_(list(st_map.keys())),
                    ConversationHistory.tool_name.in_(list(self.CALL_TOOL_NAMES)),
                )
                .distinct()
                .all()
            )
            call_props = {r.property_id for r in calls}

        return set(st_map.keys()) - call_props

    def _get_overdue_tasks(self, db: Session, prop_ids: list[int], now: datetime) -> dict[int, list[str]]:
        rows = (
            db.query(ScheduledTask.property_id, ScheduledTask.title)
            .filter(
                ScheduledTask.property_id.in_(prop_ids),
                ScheduledTask.task_type == TaskType.FOLLOW_UP,
                ScheduledTask.status == TaskStatus.PENDING,
                ScheduledTask.scheduled_at <= now,
                ScheduledTask.action != "snooze_follow_up",
            )
            .all()
        )
        result: dict[int, list[str]] = {}
        for r in rows:
            result.setdefault(r.property_id, []).append(r.title)
        return result

    def _get_missing_contacts(self, db: Session, prop_ids: list[int]) -> set[int]:
        pending_ids = set(prop_ids)
        buyer_props = (
            db.query(Contact.property_id)
            .filter(
                Contact.property_id.in_(list(pending_ids)),
                Contact.role == ContactRole.BUYER,
            )
            .distinct()
            .all()
        )
        has_buyer = {r.property_id for r in buyer_props}
        return pending_ids - has_buyer

    # ── Scoring ──

    def _score_property(
        self, prop, now, recent_cutoff, last_activities, snoozed_ids,
        unsigned_contracts, deadline_contracts, skip_no_outreach,
        overdue_tasks, missing_contacts,
    ) -> dict | None:
        if prop.id in snoozed_ids:
            return None

        last_activity = last_activities.get(prop.id)
        last_touch = last_activity or prop.created_at
        if last_touch is None:
            return None
        if last_touch.tzinfo is None:
            last_touch = last_touch.replace(tzinfo=timezone.utc)

        # Skip recently touched
        if last_touch > recent_cutoff:
            return None

        # Base score from staleness
        days_inactive = (now - last_touch).total_seconds() / 86400
        base_score = min(days_inactive * 10, self.MAX_BASE_SCORE)

        # Deal grade multiplier
        grade = (prop.score_grade or "").upper()
        multiplier = self.GRADE_MULTIPLIERS.get(grade, 1.0)
        score = base_score * multiplier

        reasons = []
        suggested_action = None
        contact_info = None

        # Bonus: approaching deadlines
        deadlines = deadline_contracts.get(prop.id, [])
        if deadlines:
            score += self.BONUS_DEADLINE
            name, days_left = deadlines[0]
            if days_left < 0:
                reasons.append(f"Contract '{name}' OVERDUE by {abs(days_left)} day(s)")
            else:
                reasons.append(f"Contract '{name}' due in {days_left} day(s)")
            suggested_action = f"Follow up on '{name}' contract"

        # Bonus: overdue tasks
        tasks = overdue_tasks.get(prop.id, [])
        if tasks:
            score += self.BONUS_OVERDUE_TASK
            reasons.append(f"Overdue task: {tasks[0]}")
            if not suggested_action:
                suggested_action = tasks[0]

        # Bonus: unsigned contracts
        unsigned = unsigned_contracts.get(prop.id, [])
        if unsigned:
            score += self.BONUS_UNSIGNED_CONTRACT
            days_label = f"{self.UNSIGNED_STALE_DAYS}+ days"
            reasons.append(f"{unsigned[0]} unsigned for {days_label}")
            if not suggested_action:
                suggested_action = f"Send or resend '{unsigned[0]}' for signature"

        # Bonus: skip trace without outreach
        if prop.id in skip_no_outreach:
            score += self.BONUS_SKIP_NO_OUTREACH
            reasons.append("Skip trace done — no outreach yet")
            if not suggested_action:
                suggested_action = "Call the property owner"

        # Bonus: missing key contacts
        if prop.status == PropertyStatus.WAITING_FOR_CONTRACTS and prop.id in missing_contacts:
            score += self.BONUS_MISSING_CONTACTS
            reasons.append("No buyer contact for property waiting for contracts")
            if not suggested_action:
                suggested_action = "Add a buyer contact"

        # Default reason if none
        if not reasons:
            reasons.append(f"No activity in {int(days_inactive)} day(s)")
            if not suggested_action:
                suggested_action = "Check in on this property"

        # Priority from score
        priority = "low"
        for level, threshold in sorted(self.SCORE_THRESHOLDS.items(), key=lambda x: -x[1]):
            if score >= threshold:
                priority = level
                break

        # Try to find best contact
        contact_info = self._get_best_contact(prop)

        # Enrich suggested action with contact phone if available
        if contact_info and contact_info.get("phone") and "Call" in (suggested_action or ""):
            suggested_action = f"Call {contact_info['name']} at {contact_info['phone']}"

        return {
            "property_id": prop.id,
            "address": f"{prop.address}, {prop.city}, {prop.state}",
            "status": prop.status.value if prop.status else "unknown",
            "deal_score": prop.deal_score,
            "score_grade": prop.score_grade,
            "score": round(score, 1),
            "priority": priority,
            "reasons": reasons,
            "suggested_action": suggested_action,
            "contact": contact_info,
            "days_since_activity": round(days_inactive, 1),
        }

    def _get_best_contact(self, prop) -> dict | None:
        if not prop.contacts:
            # Check skip traces for owner info
            if prop.skip_traces:
                st = prop.skip_traces[0]
                phones = st.phone_numbers or []
                phone = phones[0].get("number") if phones else None
                if st.owner_name:
                    return {"name": st.owner_name, "phone": phone, "role": "owner"}
            return None

        # Prefer buyer, then seller, then first contact
        for preferred in [ContactRole.BUYER, ContactRole.SELLER]:
            for c in prop.contacts:
                if c.role == preferred:
                    return {"name": c.name, "phone": c.phone, "role": c.role.value}

        c = prop.contacts[0]
        return {"name": c.name, "phone": c.phone, "role": c.role.value if c.role else "other"}

    # ── Voice summary ──

    def _build_voice_summary(self, items: list[dict], total: int) -> str:
        if not items:
            return "No follow-ups needed right now. All properties are up to date."

        parts = [f"You have {total} follow-up{'s' if total != 1 else ''}."]

        top = items[0]
        address = top["address"].split(",")[0]
        reason = top["reasons"][0] if top["reasons"] else "needs attention"
        action = top.get("suggested_action", "follow up")
        parts.append(f"Top priority: {address} — {reason}. Suggested: {action}.")

        if len(items) > 1:
            second = items[1]
            addr2 = second["address"].split(",")[0]
            reason2 = second["reasons"][0] if second["reasons"] else "needs attention"
            parts.append(f"Second: {addr2} — {reason2}.")

        return " ".join(parts)


follow_up_queue_service = FollowUpQueueService()
