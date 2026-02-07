"""Voice campaign orchestration service.

Implements campaign lifecycle, target enrollment, queue processing, retries,
and webhook-driven outcome updates for Vapi outbound calls.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.contact import Contact
from app.models.property import Property
from app.models.voice_campaign import VoiceCampaign, VoiceCampaignTarget
from app.services.vapi_service import vapi_service

logger = logging.getLogger(__name__)


class CampaignStatus:
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELED = "canceled"


class CampaignTargetStatus:
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXHAUSTED = "exhausted"
    CANCELED = "canceled"


class VoiceCampaignService:
    def __init__(self):
        self._process_lock = asyncio.Lock()

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _normalize_phone(raw: str | None) -> str | None:
        if not raw:
            return None
        candidate = raw.strip()
        if not candidate:
            return None
        if candidate.startswith("+"):
            digits = "".join(ch for ch in candidate[1:] if ch.isdigit())
            return f"+{digits}" if digits else None

        digits = "".join(ch for ch in candidate if ch.isdigit())
        if len(digits) == 10:
            return f"+1{digits}"
        if len(digits) == 11 and digits.startswith("1"):
            return f"+{digits}"
        if len(digits) >= 8:
            return f"+{digits}"
        return None

    @staticmethod
    def _normalize_roles(roles: list[str] | None) -> list[str] | None:
        if not roles:
            return None
        normalized = sorted({r.strip().lower() for r in roles if r and r.strip()})
        return normalized or None

    def create_campaign(
        self,
        db: Session,
        *,
        name: str,
        description: str | None,
        call_purpose: str,
        property_id: int | None,
        contact_roles: list[str] | None,
        max_attempts: int,
        retry_delay_minutes: int,
        rate_limit_per_minute: int,
        assistant_overrides: dict[str, Any] | None,
    ) -> VoiceCampaign:
        campaign = VoiceCampaign(
            name=name,
            description=description,
            status=CampaignStatus.DRAFT,
            call_purpose=call_purpose,
            property_id=property_id,
            contact_roles=self._normalize_roles(contact_roles),
            max_attempts=max_attempts,
            retry_delay_minutes=retry_delay_minutes,
            rate_limit_per_minute=rate_limit_per_minute,
            assistant_overrides=assistant_overrides,
        )
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        return campaign

    def get_campaign(self, db: Session, campaign_id: int) -> VoiceCampaign | None:
        return db.query(VoiceCampaign).filter(VoiceCampaign.id == campaign_id).first()

    def list_campaigns(self, db: Session, status: str | None = None, limit: int = 100) -> list[VoiceCampaign]:
        query = db.query(VoiceCampaign)
        if status:
            query = query.filter(VoiceCampaign.status == status.lower().strip())
        return query.order_by(VoiceCampaign.created_at.desc()).limit(limit).all()

    def update_campaign(self, db: Session, campaign: VoiceCampaign, updates: dict[str, Any]) -> VoiceCampaign:
        allowed = {
            "name",
            "description",
            "call_purpose",
            "property_id",
            "contact_roles",
            "max_attempts",
            "retry_delay_minutes",
            "rate_limit_per_minute",
            "assistant_overrides",
            "status",
        }
        for key, value in updates.items():
            if key not in allowed:
                continue
            if key == "contact_roles":
                value = self._normalize_roles(value)
            if key == "status" and isinstance(value, str):
                value = value.lower().strip()
            setattr(campaign, key, value)

        db.commit()
        db.refresh(campaign)
        return campaign

    def cancel_campaign(self, db: Session, campaign: VoiceCampaign) -> VoiceCampaign:
        now = self._utcnow()
        campaign.status = CampaignStatus.CANCELED
        campaign.completed_at = now

        db.query(VoiceCampaignTarget).filter(
            VoiceCampaignTarget.campaign_id == campaign.id,
            VoiceCampaignTarget.status.in_([CampaignTargetStatus.QUEUED, CampaignTargetStatus.IN_PROGRESS]),
        ).update(
            {
                VoiceCampaignTarget.status: CampaignTargetStatus.CANCELED,
                VoiceCampaignTarget.completed_at: now,
                VoiceCampaignTarget.last_disposition: "campaign_canceled",
            },
            synchronize_session=False,
        )
        db.commit()
        db.refresh(campaign)
        return campaign

    def _target_summary(self, campaign_id: int, requested: int, added: int, skipped_existing: int, skipped_invalid: int) -> dict[str, int]:
        return {
            "campaign_id": campaign_id,
            "requested": requested,
            "added": added,
            "skipped_existing": skipped_existing,
            "skipped_invalid": skipped_invalid,
        }

    def _add_target_if_new(
        self,
        db: Session,
        *,
        campaign: VoiceCampaign,
        existing_phones: set[str],
        phone_number: str | None,
        contact_id: int | None,
        contact_name: str | None,
        property_id: int | None,
    ) -> tuple[bool, str]:
        normalized = self._normalize_phone(phone_number)
        if not normalized:
            return False, "invalid"
        if normalized in existing_phones:
            return False, "existing"

        target = VoiceCampaignTarget(
            campaign_id=campaign.id,
            contact_id=contact_id,
            property_id=property_id,
            contact_name=contact_name,
            phone_number=normalized,
            status=CampaignTargetStatus.QUEUED,
            attempts_made=0,
            next_attempt_at=self._utcnow(),
        )
        db.add(target)
        existing_phones.add(normalized)
        return True, "added"

    def add_targets_manual(
        self,
        db: Session,
        *,
        campaign: VoiceCampaign,
        contact_ids: list[int],
        phone_numbers: list[str],
        property_id: int | None,
    ) -> dict[str, int]:
        contact_ids = list(dict.fromkeys(contact_ids))
        phone_numbers = list(dict.fromkeys(phone_numbers))

        existing_phones = {
            row[0]
            for row in db.query(VoiceCampaignTarget.phone_number)
            .filter(VoiceCampaignTarget.campaign_id == campaign.id)
            .all()
        }

        added = 0
        skipped_existing = 0
        skipped_invalid = 0

        contacts = []
        if contact_ids:
            contacts = db.query(Contact).filter(Contact.id.in_(contact_ids)).all()

        for contact in contacts:
            ok, reason = self._add_target_if_new(
                db,
                campaign=campaign,
                existing_phones=existing_phones,
                phone_number=contact.phone,
                contact_id=contact.id,
                contact_name=contact.name,
                property_id=property_id or contact.property_id or campaign.property_id,
            )
            if ok:
                added += 1
            elif reason == "existing":
                skipped_existing += 1
            else:
                skipped_invalid += 1

        for phone in phone_numbers:
            ok, reason = self._add_target_if_new(
                db,
                campaign=campaign,
                existing_phones=existing_phones,
                phone_number=phone,
                contact_id=None,
                contact_name=None,
                property_id=property_id or campaign.property_id,
            )
            if ok:
                added += 1
            elif reason == "existing":
                skipped_existing += 1
            else:
                skipped_invalid += 1

        db.commit()

        requested = len(contact_ids) + len(phone_numbers)
        return self._target_summary(campaign.id, requested, added, skipped_existing, skipped_invalid)

    def add_targets_from_filters(
        self,
        db: Session,
        *,
        campaign: VoiceCampaign,
        property_id: int | None,
        contact_roles: list[str] | None,
        limit: int,
    ) -> dict[str, int]:
        roles = self._normalize_roles(contact_roles) or campaign.contact_roles

        query = db.query(Contact).filter(Contact.phone.isnot(None))
        if property_id:
            query = query.filter(Contact.property_id == property_id)
        elif campaign.property_id:
            query = query.filter(Contact.property_id == campaign.property_id)

        contacts = query.order_by(Contact.id.asc()).limit(limit).all()

        if roles:
            role_set = {r.lower() for r in roles}
            contacts = [c for c in contacts if c.role and c.role.value.lower() in role_set]

        existing_phones = {
            row[0]
            for row in db.query(VoiceCampaignTarget.phone_number)
            .filter(VoiceCampaignTarget.campaign_id == campaign.id)
            .all()
        }

        added = 0
        skipped_existing = 0
        skipped_invalid = 0

        for contact in contacts:
            ok, reason = self._add_target_if_new(
                db,
                campaign=campaign,
                existing_phones=existing_phones,
                phone_number=contact.phone,
                contact_id=contact.id,
                contact_name=contact.name,
                property_id=contact.property_id,
            )
            if ok:
                added += 1
            elif reason == "existing":
                skipped_existing += 1
            else:
                skipped_invalid += 1

        db.commit()
        return self._target_summary(campaign.id, len(contacts), added, skipped_existing, skipped_invalid)

    def start_campaign(self, db: Session, campaign: VoiceCampaign) -> VoiceCampaign:
        if campaign.status == CampaignStatus.COMPLETED:
            raise ValueError("Cannot start a completed campaign")
        if campaign.status == CampaignStatus.CANCELED:
            raise ValueError("Cannot start a canceled campaign")

        now = self._utcnow()
        campaign.status = CampaignStatus.ACTIVE
        campaign.started_at = campaign.started_at or now
        campaign.completed_at = None

        db.query(VoiceCampaignTarget).filter(
            VoiceCampaignTarget.campaign_id == campaign.id,
            VoiceCampaignTarget.status == CampaignTargetStatus.CANCELED,
        ).update(
            {
                VoiceCampaignTarget.status: CampaignTargetStatus.QUEUED,
                VoiceCampaignTarget.next_attempt_at: now,
                VoiceCampaignTarget.completed_at: None,
                VoiceCampaignTarget.last_disposition: "resumed",
            },
            synchronize_session=False,
        )

        db.commit()
        db.refresh(campaign)
        return campaign

    def pause_campaign(self, db: Session, campaign: VoiceCampaign) -> VoiceCampaign:
        if campaign.status != CampaignStatus.ACTIVE:
            return campaign

        campaign.status = CampaignStatus.PAUSED
        db.commit()
        db.refresh(campaign)
        return campaign

    def resume_campaign(self, db: Session, campaign: VoiceCampaign) -> VoiceCampaign:
        if campaign.status not in {CampaignStatus.PAUSED, CampaignStatus.DRAFT}:
            return campaign

        campaign.status = CampaignStatus.ACTIVE
        if not campaign.started_at:
            campaign.started_at = self._utcnow()
        db.commit()
        db.refresh(campaign)
        return campaign

    def list_targets(self, db: Session, campaign_id: int, status: str | None = None, limit: int = 500) -> list[VoiceCampaignTarget]:
        query = db.query(VoiceCampaignTarget).filter(VoiceCampaignTarget.campaign_id == campaign_id)
        if status:
            query = query.filter(VoiceCampaignTarget.status == status.lower().strip())
        return query.order_by(VoiceCampaignTarget.id.asc()).limit(limit).all()

    def _resolve_target_property(self, db: Session, campaign: VoiceCampaign, target: VoiceCampaignTarget) -> Property | None:
        property_id = target.property_id or campaign.property_id
        if not property_id and target.contact_id:
            contact = db.query(Contact).filter(Contact.id == target.contact_id).first()
            if contact:
                property_id = contact.property_id

        if not property_id:
            return None
        return db.query(Property).filter(Property.id == property_id).first()

    def _schedule_retry_or_exhaust(
        self,
        *,
        campaign: VoiceCampaign,
        target: VoiceCampaignTarget,
        now: datetime,
        error: str,
    ) -> str:
        remaining = campaign.max_attempts - target.attempts_made
        if remaining > 0:
            target.status = CampaignTargetStatus.QUEUED
            target.next_attempt_at = now + timedelta(minutes=campaign.retry_delay_minutes)
            target.last_disposition = "retry_scheduled"
            target.last_error = error
            return "retry"

        target.status = CampaignTargetStatus.EXHAUSTED
        target.completed_at = now
        target.last_disposition = "exhausted"
        target.last_error = error
        return "exhausted"

    async def _process_target_attempt(
        self,
        db: Session,
        *,
        campaign: VoiceCampaign,
        target: VoiceCampaignTarget,
        now: datetime,
    ) -> str:
        prop = self._resolve_target_property(db, campaign, target)
        if not prop:
            target.attempts_made += 1
            result = self._schedule_retry_or_exhaust(
                campaign=campaign,
                target=target,
                now=now,
                error="No property context available for target",
            )
            return result

        target.attempts_made += 1
        target.last_attempt_at = now
        target.last_error = None

        context: dict[str, Any] = {
            "campaign_id": campaign.id,
            "campaign_target_id": target.id,
            "campaign_name": campaign.name,
        }
        if target.contact_name:
            context["contact_name"] = target.contact_name

        try:
            response = await vapi_service.make_property_call(
                db=db,
                property=prop,
                phone_number=target.phone_number,
                call_purpose=campaign.call_purpose,
                assistant_config=campaign.assistant_overrides,
                custom_context=context,
            )
        except Exception as exc:
            logger.warning("Campaign %s target %s call failed: %s", campaign.id, target.id, exc)
            return self._schedule_retry_or_exhaust(
                campaign=campaign,
                target=target,
                now=now,
                error=f"Call initiation failed: {exc}",
            )

        target.status = CampaignTargetStatus.IN_PROGRESS
        target.last_call_id = response.get("call_id")
        target.last_call_status = response.get("status")
        target.last_disposition = "dialing"
        target.last_error = None
        return "started"

    def _refresh_campaign_completion(self, db: Session, campaign: VoiceCampaign) -> None:
        pending = db.query(VoiceCampaignTarget).filter(
            VoiceCampaignTarget.campaign_id == campaign.id,
            VoiceCampaignTarget.status.in_([
                CampaignTargetStatus.QUEUED,
                CampaignTargetStatus.IN_PROGRESS,
            ]),
        ).count()

        if pending == 0 and campaign.status == CampaignStatus.ACTIVE:
            campaign.status = CampaignStatus.COMPLETED
            campaign.completed_at = self._utcnow()

    async def process_campaign_once(
        self,
        db: Session,
        *,
        campaign: VoiceCampaign,
        max_calls: int,
    ) -> dict[str, int]:
        now = self._utcnow()
        campaign.last_run_at = now

        budget = max(1, min(max_calls, campaign.rate_limit_per_minute))
        targets = (
            db.query(VoiceCampaignTarget)
            .filter(
                VoiceCampaignTarget.campaign_id == campaign.id,
                VoiceCampaignTarget.status == CampaignTargetStatus.QUEUED,
                VoiceCampaignTarget.next_attempt_at <= now,
            )
            .order_by(VoiceCampaignTarget.next_attempt_at.asc(), VoiceCampaignTarget.id.asc())
            .limit(budget)
            .all()
        )

        summary = {
            "targets_processed": 0,
            "calls_started": 0,
            "retries_scheduled": 0,
            "exhausted": 0,
        }

        for target in targets:
            summary["targets_processed"] += 1
            result = await self._process_target_attempt(db, campaign=campaign, target=target, now=now)
            if result == "started":
                summary["calls_started"] += 1
            elif result == "retry":
                summary["retries_scheduled"] += 1
            elif result == "exhausted":
                summary["exhausted"] += 1

            db.commit()

        self._refresh_campaign_completion(db, campaign)
        db.commit()
        return summary

    async def process_campaign_once_locked(
        self,
        db: Session,
        *,
        campaign: VoiceCampaign,
        max_calls: int,
    ) -> dict[str, int]:
        async with self._process_lock:
            return await self.process_campaign_once(
                db,
                campaign=campaign,
                max_calls=max_calls,
            )

    async def process_active_campaigns_once(self, max_calls_per_campaign: int = 5) -> dict[str, int]:
        async with self._process_lock:
            db = SessionLocal()
            try:
                campaigns = (
                    db.query(VoiceCampaign)
                    .filter(VoiceCampaign.status == CampaignStatus.ACTIVE)
                    .order_by(VoiceCampaign.id.asc())
                    .all()
                )

                summary = {
                    "campaigns_scanned": len(campaigns),
                    "targets_processed": 0,
                    "calls_started": 0,
                    "retries_scheduled": 0,
                    "exhausted": 0,
                }

                for campaign in campaigns:
                    result = await self.process_campaign_once(
                        db,
                        campaign=campaign,
                        max_calls=max_calls_per_campaign,
                    )
                    for key in ["targets_processed", "calls_started", "retries_scheduled", "exhausted"]:
                        summary[key] += result.get(key, 0)

                return summary
            finally:
                db.close()

    @staticmethod
    def _extract_nested(payload: dict[str, Any], *paths: tuple[str, ...]) -> Any:
        for path in paths:
            current: Any = payload
            ok = True
            for part in path:
                if not isinstance(current, dict) or part not in current:
                    ok = False
                    break
                current = current[part]
            if ok:
                return current
        return None

    def _extract_webhook_info(self, payload: dict[str, Any]) -> dict[str, Any]:
        call = payload.get("call") if isinstance(payload.get("call"), dict) else {}
        message = payload.get("message") if isinstance(payload.get("message"), dict) else {}
        message_call = message.get("call") if isinstance(message.get("call"), dict) else {}

        call_id = (
            payload.get("call_id")
            or payload.get("callId")
            or payload.get("id")
            or call.get("id")
            or message.get("callId")
            or message_call.get("id")
        )

        call_status = (
            payload.get("status")
            or call.get("status")
            or message.get("status")
            or message_call.get("status")
        )

        ended_reason = (
            payload.get("endedReason")
            or payload.get("ended_reason")
            or call.get("endedReason")
            or message_call.get("endedReason")
        )

        event_type = (
            payload.get("type")
            or message.get("type")
            or payload.get("event")
        )

        metadata = (
            self._extract_nested(payload, ("assistant", "metadata"))
            or self._extract_nested(payload, ("metadata",))
            or self._extract_nested(payload, ("call", "assistant", "metadata"))
            or self._extract_nested(payload, ("message", "call", "assistant", "metadata"))
            or {}
        )
        if not isinstance(metadata, dict):
            metadata = {}

        raw_target_id = metadata.get("campaign_target_id") or metadata.get("campaignTargetId")
        campaign_target_id = None
        if raw_target_id is not None:
            try:
                campaign_target_id = int(raw_target_id)
            except (TypeError, ValueError):
                campaign_target_id = None

        return {
            "call_id": str(call_id) if call_id is not None else None,
            "call_status": str(call_status).lower() if call_status is not None else None,
            "ended_reason": str(ended_reason).lower() if ended_reason is not None else None,
            "event_type": str(event_type).lower() if event_type is not None else None,
            "campaign_target_id": campaign_target_id,
            "metadata": metadata,
        }

    @staticmethod
    def _classify_webhook_outcome(call_status: str | None, ended_reason: str | None, event_type: str | None) -> str | None:
        non_terminal_statuses = {"queued", "ringing", "in-progress", "in_progress", "active"}
        if call_status in non_terminal_statuses:
            return None

        terminal_signal = bool(
            (call_status and call_status in {"ended", "completed", "failed", "canceled", "cancelled"})
            or (event_type and any(token in event_type for token in ["ended", "completed", "hang", "report"]))
            or ended_reason
        )
        if not terminal_signal:
            return None

        failure_tokens = {
            "busy",
            "no-answer",
            "no_answer",
            "voicemail",
            "failed",
            "error",
            "canceled",
            "cancelled",
            "rejected",
            "timeout",
            "unanswered",
        }

        reason = ended_reason or ""
        if any(token in reason for token in failure_tokens):
            return "retry"

        if call_status in {"failed", "canceled", "cancelled"}:
            return "retry"

        return "completed"

    def handle_vapi_webhook(self, db: Session, payload: dict[str, Any]) -> dict[str, Any]:
        info = self._extract_webhook_info(payload)

        target = None
        if info["campaign_target_id"]:
            target = db.query(VoiceCampaignTarget).filter(VoiceCampaignTarget.id == info["campaign_target_id"]).first()

        if not target and info["call_id"]:
            target = (
                db.query(VoiceCampaignTarget)
                .filter(VoiceCampaignTarget.last_call_id == info["call_id"])
                .order_by(VoiceCampaignTarget.id.desc())
                .first()
            )

        if not target:
            return {
                "matched": False,
                "message": "No campaign target found for webhook payload",
                "call_id": info["call_id"],
            }

        campaign = db.query(VoiceCampaign).filter(VoiceCampaign.id == target.campaign_id).first()
        if not campaign:
            return {
                "matched": False,
                "message": "Campaign not found for matched target",
                "target_id": target.id,
            }

        now = self._utcnow()
        target.last_webhook_payload = payload
        if info["call_status"]:
            target.last_call_status = info["call_status"]
        if info["call_id"] and not target.last_call_id:
            target.last_call_id = info["call_id"]

        outcome = self._classify_webhook_outcome(
            call_status=info["call_status"],
            ended_reason=info["ended_reason"],
            event_type=info["event_type"],
        )

        if outcome == "completed":
            target.status = CampaignTargetStatus.COMPLETED
            target.completed_at = now
            target.last_disposition = "completed"
            target.last_error = None
        elif outcome == "retry":
            error = f"Call outcome requires retry (status={info['call_status']}, reason={info['ended_reason']})"
            self._schedule_retry_or_exhaust(
                campaign=campaign,
                target=target,
                now=now,
                error=error,
            )
        else:
            target.last_disposition = target.last_disposition or "progress_update"

        self._refresh_campaign_completion(db, campaign)
        db.commit()

        return {
            "matched": True,
            "campaign_id": campaign.id,
            "target_id": target.id,
            "target_status": target.status,
            "outcome": outcome or "progress",
            "call_id": info["call_id"],
        }

    def get_campaign_analytics(self, db: Session, campaign: VoiceCampaign) -> dict[str, Any]:
        targets = db.query(VoiceCampaignTarget).filter(VoiceCampaignTarget.campaign_id == campaign.id).all()

        totals = {
            "total": len(targets),
            CampaignTargetStatus.QUEUED: 0,
            CampaignTargetStatus.IN_PROGRESS: 0,
            CampaignTargetStatus.COMPLETED: 0,
            CampaignTargetStatus.EXHAUSTED: 0,
            CampaignTargetStatus.CANCELED: 0,
        }

        attempts_sum = 0
        for target in targets:
            if target.status in totals:
                totals[target.status] += 1
            attempts_sum += int(target.attempts_made or 0)

        total = totals["total"]
        success_rate = float(totals[CampaignTargetStatus.COMPLETED] / total) if total else 0.0
        avg_attempts = float(attempts_sum / total) if total else 0.0

        return {
            "campaign_id": campaign.id,
            "campaign_status": campaign.status,
            "totals": totals,
            "success_rate": round(success_rate, 4),
            "avg_attempts": round(avg_attempts, 2),
            "last_run_at": campaign.last_run_at,
        }


voice_campaign_service = VoiceCampaignService()


async def run_campaign_worker_loop(interval_seconds: int = 15, max_calls_per_campaign: int = 5) -> None:
    """Background loop that processes active campaigns on an interval."""
    while True:
        try:
            summary = await voice_campaign_service.process_active_campaigns_once(
                max_calls_per_campaign=max_calls_per_campaign,
            )
            if summary["targets_processed"] > 0:
                logger.info("Campaign worker tick: %s", summary)
        except Exception as exc:  # pragma: no cover - runtime safety net
            logger.exception("Campaign worker tick failed: %s", exc)

        await asyncio.sleep(interval_seconds)
