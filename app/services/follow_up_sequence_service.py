"""Auto Follow-Up Sequence Service — multi-channel drip that adapts to engagement."""

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any

import httpx
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.follow_up_sequence import (
    FollowUpSequence, SequenceTouch, SequenceStatus,
    TouchChannel, TouchStatus, LeadTemperature,
)

logger = logging.getLogger(__name__)

# ── Sequence Templates ──
# Each template defines the touches: (day_offset, channel)
SEQUENCE_TEMPLATES = {
    "default": {
        "name": "Standard Lead Nurture",
        "description": "7-touch sequence over 30 days: email → SMS → call → postcard → email → SMS → call",
        "steps": [
            (0, TouchChannel.EMAIL, "Introduction + value prop"),
            (3, TouchChannel.SMS, "Quick check-in"),
            (7, TouchChannel.CALL, "Personal call"),
            (14, TouchChannel.POSTCARD, "Branded postcard with market stats"),
            (21, TouchChannel.EMAIL, "Market update + new listings"),
            (25, TouchChannel.SMS, "Availability check"),
            (30, TouchChannel.CALL, "Final follow-up call"),
        ],
    },
    "hot_lead": {
        "name": "Hot Lead Fast Track",
        "description": "5-touch aggressive sequence over 7 days",
        "steps": [
            (0, TouchChannel.EMAIL, "Immediate response with property details"),
            (0, TouchChannel.SMS, "Quick intro text"),
            (1, TouchChannel.CALL, "Personal call next day"),
            (3, TouchChannel.EMAIL, "Comp report + market analysis"),
            (7, TouchChannel.CALL, "Follow-up call with next steps"),
        ],
    },
    "cold_lead": {
        "name": "Cold Lead Warm-Up",
        "description": "5-touch gentle sequence over 60 days",
        "steps": [
            (0, TouchChannel.EMAIL, "Soft intro + market snapshot"),
            (14, TouchChannel.POSTCARD, "Branded postcard"),
            (30, TouchChannel.EMAIL, "Market update + helpful content"),
            (45, TouchChannel.SMS, "Quick check-in"),
            (60, TouchChannel.CALL, "Exploratory call"),
        ],
    },
    "seller": {
        "name": "Seller Outreach",
        "description": "6-touch sequence targeting potential sellers",
        "steps": [
            (0, TouchChannel.POSTCARD, "What's your home worth? CMA offer"),
            (5, TouchChannel.EMAIL, "Neighborhood market report"),
            (10, TouchChannel.CALL, "Intro call — free home valuation"),
            (20, TouchChannel.POSTCARD, "Recent sales in your area"),
            (30, TouchChannel.EMAIL, "Success story + testimonial"),
            (45, TouchChannel.CALL, "Check-in call"),
        ],
    },
    "past_client": {
        "name": "Past Client Stay-in-Touch",
        "description": "4-touch quarterly check-in",
        "steps": [
            (0, TouchChannel.EMAIL, "Home anniversary + neighborhood update"),
            (90, TouchChannel.POSTCARD, "Seasonal greeting"),
            (180, TouchChannel.EMAIL, "Market update + referral ask"),
            (270, TouchChannel.POSTCARD, "Holiday card"),
        ],
    },
}


class FollowUpSequenceService:

    def __init__(self):
        self._anthropic_key = None

    @property
    def anthropic_key(self) -> str:
        if not self._anthropic_key:
            from app.config import settings
            self._anthropic_key = settings.anthropic_api_key
        return self._anthropic_key

    # ── Create Sequence ──

    def create_sequence(
        self,
        db: Session,
        lead_name: str,
        lead_email: str = None,
        lead_phone: str = None,
        lead_source: str = None,
        template_name: str = "default",
        property_id: int = None,
        contact_id: int = None,
        temperature: LeadTemperature = LeadTemperature.WARM,
        custom_context: str = None,
    ) -> FollowUpSequence:
        """Create a new follow-up sequence for a lead."""

        # Auto-select template based on temperature if using default
        if template_name == "default":
            if temperature == LeadTemperature.HOT:
                template_name = "hot_lead"
            elif temperature == LeadTemperature.COLD:
                template_name = "cold_lead"

        template = SEQUENCE_TEMPLATES.get(template_name, SEQUENCE_TEMPLATES["default"])
        steps = template["steps"]
        now = datetime.now(timezone.utc)

        # Create sequence
        sequence = FollowUpSequence(
            name=f"{template['name']} — {lead_name}",
            contact_id=contact_id,
            property_id=property_id,
            lead_name=lead_name,
            lead_email=lead_email,
            lead_phone=lead_phone,
            lead_source=lead_source,
            lead_temperature=temperature,
            template_name=template_name,
            status=SequenceStatus.ACTIVE,
            current_step=0,
            total_steps=len(steps),
        )
        db.add(sequence)
        db.flush()

        # Create touches
        property_context = self._get_property_context(db, property_id) if property_id else ""
        first_touch_time = None

        for i, (day_offset, channel, description) in enumerate(steps):
            touch_time = now + timedelta(days=day_offset)
            if i == 0:
                first_touch_time = touch_time

            # Skip channels we can't deliver on
            if channel == TouchChannel.EMAIL and not lead_email:
                continue
            if channel in (TouchChannel.SMS, TouchChannel.CALL, TouchChannel.RINGLESS_VM) and not lead_phone:
                continue

            # Generate personalized message via Claude
            message = self._generate_message(
                channel=channel,
                lead_name=lead_name,
                description=description,
                step_number=i + 1,
                total_steps=len(steps),
                property_context=property_context,
                custom_context=custom_context,
                temperature=temperature.value,
            )

            subject = None
            if channel == TouchChannel.EMAIL:
                subject = self._generate_subject(lead_name, description, i + 1)

            touch = SequenceTouch(
                sequence_id=sequence.id,
                step_number=i,
                channel=channel,
                delay_days=day_offset,
                subject=subject,
                message=message,
                status=TouchStatus.SCHEDULED,
                scheduled_at=touch_time,
            )
            db.add(touch)

        sequence.next_touch_at = first_touch_time
        db.commit()
        db.refresh(sequence)

        logger.info(f"Created sequence '{sequence.name}' with {sequence.total_steps} steps")

        # Send Telegram notification
        self._send_telegram(
            f"New follow-up sequence started:\n"
            f"Lead: {lead_name}\n"
            f"Template: {template['name']}\n"
            f"Steps: {len(steps)} touches over {steps[-1][0]} days\n"
            f"First touch: Now" if steps[0][0] == 0 else f"First touch: Day {steps[0][0]}"
        )

        return sequence

    # ── Process Due Touches ──

    def process_due_touches(self, db: Session) -> List[Dict[str, Any]]:
        """Process all touches that are due. Called by cron/heartbeat."""
        now = datetime.now(timezone.utc)

        due_touches = db.query(SequenceTouch).join(FollowUpSequence).filter(
            and_(
                FollowUpSequence.status == SequenceStatus.ACTIVE,
                SequenceTouch.status == TouchStatus.SCHEDULED,
                SequenceTouch.scheduled_at <= now,
            )
        ).order_by(SequenceTouch.scheduled_at).limit(20).all()

        results = []
        for touch in due_touches:
            result = self._execute_touch(db, touch)
            results.append(result)

        return results

    def _execute_touch(self, db: Session, touch: SequenceTouch) -> Dict[str, Any]:
        """Execute a single touch — send the email/SMS/call/postcard."""
        sequence = touch.sequence
        result = {"touch_id": touch.id, "channel": touch.channel.value, "lead": sequence.lead_name}

        try:
            if touch.channel == TouchChannel.EMAIL:
                self._send_email(sequence, touch)
                sequence.emails_sent = (sequence.emails_sent or 0) + 1

            elif touch.channel == TouchChannel.SMS:
                self._send_sms(sequence, touch)
                sequence.sms_sent = (sequence.sms_sent or 0) + 1

            elif touch.channel == TouchChannel.CALL:
                self._make_call(sequence, touch)
                sequence.calls_made = (sequence.calls_made or 0) + 1

            elif touch.channel == TouchChannel.POSTCARD:
                self._send_postcard(sequence, touch)
                sequence.postcards_sent = (sequence.postcards_sent or 0) + 1

            touch.status = TouchStatus.SENT
            touch.sent_at = datetime.now(timezone.utc)
            result["status"] = "sent"

        except Exception as e:
            touch.status = TouchStatus.FAILED
            touch.error_message = str(e)[:500]
            result["status"] = "failed"
            result["error"] = str(e)[:200]
            logger.error(f"Touch {touch.id} failed: {e}")

        # Update sequence progress
        sequence.current_step = touch.step_number + 1
        self._update_next_touch(db, sequence)
        self._update_engagement_score(db, sequence)

        db.commit()
        return result

    # ── Engagement-Based Adaptation ──

    def record_engagement(
        self, db: Session, sequence_id: int, event: str
    ) -> Dict[str, Any]:
        """Record engagement event and adapt the sequence.

        Events: email_opened, email_replied, sms_replied, call_answered, call_voicemail
        """
        sequence = db.query(FollowUpSequence).filter(FollowUpSequence.id == sequence_id).first()
        if not sequence:
            return {"error": "Sequence not found"}

        if event == "email_opened":
            sequence.emails_opened = (sequence.emails_opened or 0) + 1
            # Mark the most recent email touch as opened
            latest_email = db.query(SequenceTouch).filter(
                SequenceTouch.sequence_id == sequence_id,
                SequenceTouch.channel == TouchChannel.EMAIL,
                SequenceTouch.status == TouchStatus.SENT,
            ).order_by(SequenceTouch.sent_at.desc()).first()
            if latest_email:
                latest_email.status = TouchStatus.OPENED
                latest_email.opened_at = datetime.now(timezone.utc)

        elif event in ("email_replied", "sms_replied"):
            sequence.replies_received = (sequence.replies_received or 0) + 1
            # Hot! Upgrade temperature and accelerate
            if sequence.lead_temperature != LeadTemperature.HOT:
                sequence.lead_temperature = LeadTemperature.HOT
                self._send_telegram(
                    f"LEAD REPLIED! {sequence.lead_name} responded.\n"
                    f"Sequence: {sequence.name}\n"
                    f"Upgraded to HOT lead."
                )

        elif event == "call_answered":
            # They picked up — great sign
            sequence.lead_temperature = LeadTemperature.HOT

        elif event == "call_voicemail":
            pass  # Normal, continue sequence

        self._update_engagement_score(db, sequence)
        db.commit()

        return {
            "sequence_id": sequence_id,
            "event": event,
            "temperature": sequence.lead_temperature.value,
            "engagement_score": sequence.engagement_score,
        }

    # ── Sequence Management ──

    def pause_sequence(self, db: Session, sequence_id: int) -> Dict:
        seq = db.query(FollowUpSequence).filter(FollowUpSequence.id == sequence_id).first()
        if not seq:
            return {"error": "Not found"}
        seq.status = SequenceStatus.PAUSED
        seq.paused_at = datetime.now(timezone.utc)
        db.commit()
        return {"message": f"Paused sequence for {seq.lead_name}", "id": sequence_id}

    def resume_sequence(self, db: Session, sequence_id: int) -> Dict:
        seq = db.query(FollowUpSequence).filter(FollowUpSequence.id == sequence_id).first()
        if not seq:
            return {"error": "Not found"}
        seq.status = SequenceStatus.ACTIVE
        seq.paused_at = None
        self._update_next_touch(db, seq)
        db.commit()
        return {"message": f"Resumed sequence for {seq.lead_name}", "id": sequence_id}

    def cancel_sequence(self, db: Session, sequence_id: int) -> Dict:
        seq = db.query(FollowUpSequence).filter(FollowUpSequence.id == sequence_id).first()
        if not seq:
            return {"error": "Not found"}
        seq.status = SequenceStatus.CANCELLED
        # Cancel pending touches
        for touch in seq.touches:
            if touch.status in (TouchStatus.PENDING, TouchStatus.SCHEDULED):
                touch.status = TouchStatus.SKIPPED
        db.commit()
        return {"message": f"Cancelled sequence for {seq.lead_name}", "id": sequence_id}

    def list_sequences(
        self, db: Session, status: Optional[SequenceStatus] = None, limit: int = 20
    ) -> List[Dict]:
        q = db.query(FollowUpSequence)
        if status:
            q = q.filter(FollowUpSequence.status == status)
        sequences = q.order_by(FollowUpSequence.created_at.desc()).limit(limit).all()
        return [self._format_sequence(s) for s in sequences]

    def get_sequence(self, db: Session, sequence_id: int) -> Optional[Dict]:
        seq = db.query(FollowUpSequence).filter(FollowUpSequence.id == sequence_id).first()
        if not seq:
            return None
        return self._format_sequence(seq, include_touches=True)

    def get_due_count(self, db: Session) -> int:
        now = datetime.now(timezone.utc)
        return db.query(SequenceTouch).join(FollowUpSequence).filter(
            and_(
                FollowUpSequence.status == SequenceStatus.ACTIVE,
                SequenceTouch.status == TouchStatus.SCHEDULED,
                SequenceTouch.scheduled_at <= now,
            )
        ).count()

    def get_templates(self) -> Dict:
        return {
            name: {
                "name": t["name"],
                "description": t["description"],
                "steps": [
                    {"day": s[0], "channel": s[1].value, "description": s[2]}
                    for s in t["steps"]
                ],
            }
            for name, t in SEQUENCE_TEMPLATES.items()
        }

    # ── Internal: Message Generation ──

    def _generate_message(
        self, channel: TouchChannel, lead_name: str, description: str,
        step_number: int, total_steps: int, property_context: str,
        custom_context: str, temperature: str,
    ) -> str:
        """Generate personalized message via Claude."""
        if not self.anthropic_key:
            return self._fallback_message(channel, lead_name, description)

        channel_guidelines = {
            TouchChannel.EMAIL: "Write a professional but warm email body. 3-4 paragraphs max. Include a clear call-to-action.",
            TouchChannel.SMS: "Write a short text message, 2-3 sentences max. Casual but professional. Include a question to prompt reply.",
            TouchChannel.CALL: "Write a brief call script/talking points. Include greeting, purpose, key points, and close.",
            TouchChannel.POSTCARD: "Write postcard copy. Short headline + 2-3 sentences. Include call-to-action with phone number.",
            TouchChannel.RINGLESS_VM: "Write a 30-second voicemail script. Friendly, brief, include callback number.",
        }

        prompt = f"""Generate a {channel.value} message for a real estate follow-up sequence.

Lead: {lead_name}
Temperature: {temperature}
Step {step_number} of {total_steps}: {description}
{f'Property context: {property_context}' if property_context else ''}
{f'Additional context: {custom_context}' if custom_context else ''}

Agent: Ed Duran, Emprezario Inc
Phone: 201-300-5189
Email: emprezarioinc@gmail.com

{channel_guidelines.get(channel, '')}

Write ONLY the message content. No headers, no metadata. Be genuine, not salesy."""

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.anthropic_key)
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Message generation failed: {e}")
            return self._fallback_message(channel, lead_name, description)

    def _generate_subject(self, lead_name: str, description: str, step: int) -> str:
        first_name = lead_name.split()[0] if lead_name else "there"
        subjects = {
            1: f"Hi {first_name} — quick question about your property search",
            2: f"{first_name}, saw something you might like",
            3: f"Market update for you, {first_name}",
            4: f"{first_name} — new listings in your area",
            5: f"Following up, {first_name}",
        }
        return subjects.get(step, f"Quick update for you, {first_name}")

    def _fallback_message(self, channel: TouchChannel, lead_name: str, description: str) -> str:
        first_name = lead_name.split()[0] if lead_name else "there"
        if channel == TouchChannel.SMS:
            return f"Hi {first_name}, this is Ed from Emprezario Inc. {description}. Would you have a few minutes to chat? — Ed 201-300-5189"
        elif channel == TouchChannel.POSTCARD:
            return f"Hi {first_name}! {description}. Let's connect — Ed Duran, Emprezario Inc | 201-300-5189"
        else:
            return f"Hi {first_name},\n\n{description}.\n\nI'd love to help with your real estate goals. Feel free to reach out anytime.\n\nBest,\nEd Duran\nEmprezario Inc\n201-300-5189"

    # ── Internal: Channel Execution ──

    def _send_email(self, sequence: FollowUpSequence, touch: SequenceTouch):
        """Send email via Resend API."""
        from app.config import settings
        if not settings.resend_api_key:
            logger.warning("No RESEND_API_KEY — skipping email")
            return

        response = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json={
                "from": f"Ed Duran <{settings.resend_from_email}>",
                "to": [sequence.lead_email],
                "subject": touch.subject or "Quick update from Ed Duran",
                "text": touch.message,
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        touch.external_id = data.get("id")

    def _send_sms(self, sequence: FollowUpSequence, touch: SequenceTouch):
        """Send SMS via internal API (Telnyx/Twilio)."""
        try:
            response = httpx.post(
                f"{os.getenv('MCP_API_BASE_URL', 'http://localhost:8000')}/api/sms/send",
                json={"to": sequence.lead_phone, "message": touch.message},
                headers={"X-API-Key": os.getenv("MCP_API_KEY", "")},
                timeout=15,
            )
            if response.status_code == 200:
                touch.external_id = response.json().get("message_id")
        except Exception as e:
            logger.warning(f"SMS send failed, logging for manual follow-up: {e}")
            self._send_telegram(f"SMS failed for {sequence.lead_name}: {touch.message[:100]}")

    def _make_call(self, sequence: FollowUpSequence, touch: SequenceTouch):
        """Schedule a call reminder (or trigger via VAPI for auto-call)."""
        # Don't auto-call — send a Telegram reminder to make the call personally
        self._send_telegram(
            f"CALL REMINDER — Sequence Step {touch.step_number + 1}\n"
            f"Lead: {sequence.lead_name}\n"
            f"Phone: {sequence.lead_phone}\n"
            f"Script:\n{touch.message[:300]}"
        )

    def _send_postcard(self, sequence: FollowUpSequence, touch: SequenceTouch):
        """Send postcard via Lob/internal API."""
        try:
            response = httpx.post(
                f"{os.getenv('MCP_API_BASE_URL', 'http://localhost:8000')}/direct-mail/postcard",
                json={
                    "to_name": sequence.lead_name,
                    "message": touch.message,
                    "property_id": sequence.property_id,
                },
                headers={"X-API-Key": os.getenv("MCP_API_KEY", "")},
                timeout=15,
            )
            if response.status_code == 200:
                touch.external_id = response.json().get("id")
        except Exception as e:
            logger.warning(f"Postcard send failed: {e}")
            self._send_telegram(f"Postcard failed for {sequence.lead_name} — send manually")

    # ── Internal: Helpers ──

    def _update_next_touch(self, db: Session, sequence: FollowUpSequence):
        next_touch = db.query(SequenceTouch).filter(
            SequenceTouch.sequence_id == sequence.id,
            SequenceTouch.status == TouchStatus.SCHEDULED,
        ).order_by(SequenceTouch.scheduled_at).first()

        if next_touch:
            sequence.next_touch_at = next_touch.scheduled_at
        else:
            sequence.status = SequenceStatus.COMPLETED
            sequence.completed_at = datetime.now(timezone.utc)
            sequence.next_touch_at = None

    def _update_engagement_score(self, db: Session, sequence: FollowUpSequence):
        """Calculate engagement score 0-100 based on interactions."""
        score = 0
        if sequence.emails_opened:
            score += min(sequence.emails_opened * 10, 30)
        if sequence.replies_received:
            score += min(sequence.replies_received * 25, 50)
        if sequence.calls_made and sequence.lead_temperature == LeadTemperature.HOT:
            score += 20
        sequence.engagement_score = min(score, 100)

    def _get_property_context(self, db: Session, property_id: int) -> str:
        from app.models.property import Property
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            return ""
        parts = [prop.address or ""]
        if prop.price:
            parts.append(f"${prop.price:,.0f}")
        if prop.bedrooms:
            parts.append(f"{prop.bedrooms}bd")
        if prop.bathrooms:
            parts.append(f"{prop.bathrooms}ba")
        return " | ".join(parts)

    def _format_sequence(self, seq: FollowUpSequence, include_touches: bool = False) -> Dict:
        data = {
            "id": seq.id,
            "name": seq.name,
            "lead_name": seq.lead_name,
            "lead_email": seq.lead_email,
            "lead_phone": seq.lead_phone,
            "temperature": seq.lead_temperature.value if seq.lead_temperature else None,
            "status": seq.status.value,
            "template": seq.template_name,
            "progress": f"{seq.current_step}/{seq.total_steps}",
            "engagement_score": seq.engagement_score,
            "stats": {
                "emails_sent": seq.emails_sent or 0,
                "emails_opened": seq.emails_opened or 0,
                "sms_sent": seq.sms_sent or 0,
                "calls_made": seq.calls_made or 0,
                "postcards_sent": seq.postcards_sent or 0,
                "replies": seq.replies_received or 0,
            },
            "next_touch_at": seq.next_touch_at.isoformat() if seq.next_touch_at else None,
            "started_at": seq.started_at.isoformat() if seq.started_at else None,
        }
        if include_touches and seq.touches:
            data["touches"] = [
                {
                    "step": t.step_number + 1,
                    "channel": t.channel.value,
                    "day": t.delay_days,
                    "status": t.status.value,
                    "subject": t.subject,
                    "message_preview": (t.message[:150] + "...") if t.message and len(t.message) > 150 else t.message,
                    "scheduled_at": t.scheduled_at.isoformat() if t.scheduled_at else None,
                    "sent_at": t.sent_at.isoformat() if t.sent_at else None,
                }
                for t in seq.touches
            ]
        return data

    def _send_telegram(self, message: str):
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if not token or not chat_id:
            return
        try:
            httpx.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
                timeout=10,
            )
        except Exception:
            pass


# Global instance
follow_up_sequence_service = FollowUpSequenceService()
