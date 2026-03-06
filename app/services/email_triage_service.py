"""
Email Auto-Triage Service

Reads incoming emails via Gmail API, classifies them using Claude,
drafts responses for leads, and sends Telegram summaries.
"""
import os
import json
import base64
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

import httpx
import anthropic

from app.config import settings

logger = logging.getLogger(__name__)

# Gmail API constants
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
GMAIL_CREDENTIALS_PATH = Path.home() / ".credentials" / "gmail_token.json"

# Classification categories
CATEGORIES = ["hot_lead", "warm_lead", "contract_update", "showing_request", "spam", "general"]

PRIORITY_MAP = {
    "hot_lead": 1,
    "warm_lead": 2,
    "showing_request": 2,
    "contract_update": 3,
    "general": 4,
    "spam": 5,
}

CLASSIFICATION_PROMPT = """You are an expert real estate email classifier for a real estate agent/investor.

Classify this email into exactly ONE of these categories:
- hot_lead: Someone actively wanting to buy/sell property NOW, expressing urgency, ready to make offers
- warm_lead: General interest in buying/selling, asking questions, early-stage inquiries
- contract_update: Updates about existing contracts, signatures, closing dates, title company updates
- showing_request: Requests to see/show a specific property, schedule a viewing or open house
- spam: Junk mail, marketing, newsletters, unrelated promotions
- general: Everything else (personal, administrative, general questions)

Also assign a priority from 1 (most urgent) to 5 (least urgent).

Email:
From: {from_name} <{from_address}>
Subject: {subject}
Body:
{body}

Respond in JSON format only:
{{"classification": "<category>", "priority": <1-5>, "reasoning": "<brief explanation>", "key_details": "<any property addresses, dates, or dollar amounts mentioned>"}}"""

DRAFT_RESPONSE_PROMPT = """You are a professional, friendly real estate agent named Ed Duran from Emprezario Inc.
You're drafting a reply to a {classification} email.

The sender's email:
From: {from_name} <{from_address}>
Subject: {subject}
Body:
{body}

Write a personalized, professional response that:
1. Acknowledges their specific interest or request
2. Shows enthusiasm and expertise
3. If they mention a property, reference it specifically
4. Suggests a next step (call, meeting, showing)
5. Includes your contact info: Ed Duran, Emprezario Inc, 201-300-5189

Keep it concise (under 200 words), warm, and action-oriented.
Do NOT include a subject line — just the body of the reply."""


class EmailTriageService:
    """Service that triages incoming emails via Gmail API + Claude classification."""

    def __init__(self):
        self._gmail_service = None
        self._gmail_available = False
        self._processed_emails: List[Dict[str, Any]] = []
        self._stats: Dict[str, int] = {cat: 0 for cat in CATEGORIES}

    # ------------------------------------------------------------------
    # Gmail connection
    # ------------------------------------------------------------------

    def _get_gmail_service(self):
        """Initialize Gmail API service using stored OAuth credentials."""
        if self._gmail_service is not None:
            return self._gmail_service

        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build

            if not GMAIL_CREDENTIALS_PATH.exists():
                logger.warning("Gmail credentials not found at %s — running in fallback mode", GMAIL_CREDENTIALS_PATH)
                return None

            creds = Credentials.from_authorized_user_file(str(GMAIL_CREDENTIALS_PATH), GMAIL_SCOPES)

            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # Save refreshed token
                GMAIL_CREDENTIALS_PATH.write_text(creds.to_json())

            self._gmail_service = build("gmail", "v1", credentials=creds)
            self._gmail_available = True
            return self._gmail_service

        except Exception as e:
            logger.error("Failed to initialise Gmail service: %s", e)
            return None

    # ------------------------------------------------------------------
    # Email fetching
    # ------------------------------------------------------------------

    async def check_new_emails(self, since_minutes: int = 30) -> List[Dict[str, Any]]:
        """Fetch recent unread emails from Gmail and triage them.

        Falls back to returning an empty list when Gmail credentials are
        unavailable (the caller can still use classify_email / draft_response
        directly).
        """
        service = self._get_gmail_service()
        if service is None:
            logger.info("Gmail service unavailable — skipping email fetch")
            return []

        after_epoch = int((datetime.utcnow() - timedelta(minutes=since_minutes)).timestamp())
        query = f"is:unread after:{after_epoch}"

        try:
            results = service.users().messages().list(userId="me", q=query, maxResults=50).execute()
            messages = results.get("messages", [])
        except Exception as e:
            logger.error("Error fetching Gmail messages: %s", e)
            return []

        triaged: List[Dict[str, Any]] = []

        for msg_stub in messages:
            try:
                msg = service.users().messages().get(userId="me", id=msg_stub["id"], format="full").execute()
                email_data = self._parse_gmail_message(msg)
                classification = await self.classify_email(email_data)
                email_data.update(classification)

                # Auto-draft for leads
                if classification["classification"] in ("hot_lead", "warm_lead"):
                    draft = await self.draft_response(email_data, classification["classification"])
                    email_data["drafted_response"] = draft

                # Telegram alerts for certain categories
                if classification["classification"] in ("hot_lead", "showing_request", "contract_update"):
                    await self._send_telegram_alert(email_data)

                self._processed_emails.append(email_data)
                self._stats[classification["classification"]] = self._stats.get(classification["classification"], 0) + 1
                triaged.append(email_data)
            except Exception as e:
                logger.error("Error processing message %s: %s", msg_stub.get("id"), e)

        # Send digest if we processed anything
        if triaged:
            digest = self.get_email_digest()
            await self.send_telegram(f"Email Triage Digest\n\n{digest}")

        return triaged

    def _parse_gmail_message(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        """Extract useful fields from a Gmail API message resource."""
        headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}

        from_raw = headers.get("from", "")
        from_name = from_raw
        from_address = from_raw
        if "<" in from_raw and ">" in from_raw:
            from_name = from_raw.split("<")[0].strip().strip('"')
            from_address = from_raw.split("<")[1].rstrip(">")

        subject = headers.get("subject", "(no subject)")

        # Get body
        body = ""
        payload = msg.get("payload", {})
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain":
                    data = part.get("body", {}).get("data", "")
                    if data:
                        body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                        break
        else:
            data = payload.get("body", {}).get("data", "")
            if data:
                body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

        return {
            "gmail_id": msg["id"],
            "from_name": from_name,
            "from_address": from_address,
            "subject": subject,
            "body": body[:3000],  # Truncate very long emails
            "body_preview": body[:500],
            "date": headers.get("date", ""),
        }

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    async def classify_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Classify an email using Claude.

        Returns dict with classification, priority, reasoning, key_details.
        """
        if not settings.anthropic_api_key:
            logger.warning("No Anthropic API key — defaulting to 'general'")
            return {"classification": "general", "priority": 4, "reasoning": "No API key available", "key_details": ""}

        prompt = CLASSIFICATION_PROMPT.format(
            from_name=email_data.get("from_name", ""),
            from_address=email_data.get("from_address", ""),
            subject=email_data.get("subject", ""),
            body=email_data.get("body", email_data.get("body_preview", "")),
        )

        try:
            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip()

            # Parse JSON from response (handle possible markdown fences)
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

            result = json.loads(text)

            # Validate classification
            if result.get("classification") not in CATEGORIES:
                result["classification"] = "general"
            result["priority"] = max(1, min(5, int(result.get("priority", PRIORITY_MAP.get(result["classification"], 4)))))

            return result

        except Exception as e:
            logger.error("Classification error: %s", e)
            return {"classification": "general", "priority": 4, "reasoning": f"Error: {e}", "key_details": ""}

    # ------------------------------------------------------------------
    # Response drafting
    # ------------------------------------------------------------------

    async def draft_response(self, email_data: Dict[str, Any], classification: str) -> str:
        """Draft a personalized reply using Claude."""
        if not settings.anthropic_api_key:
            return ""

        prompt = DRAFT_RESPONSE_PROMPT.format(
            classification=classification.replace("_", " "),
            from_name=email_data.get("from_name", ""),
            from_address=email_data.get("from_address", ""),
            subject=email_data.get("subject", ""),
            body=email_data.get("body", email_data.get("body_preview", "")),
        )

        try:
            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        except Exception as e:
            logger.error("Draft response error: %s", e)
            return ""

    # ------------------------------------------------------------------
    # Telegram notifications
    # ------------------------------------------------------------------

    async def send_telegram(self, message: str) -> bool:
        """Send a message via Telegram bot."""
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

        if not bot_token or not chat_id:
            logger.warning("Telegram credentials not configured — skipping notification")
            return False

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json={
                    "chat_id": chat_id,
                    "text": message[:4096],  # Telegram message limit
                    "parse_mode": "HTML",
                }, timeout=15.0)
                resp.raise_for_status()
                return True
        except Exception as e:
            logger.error("Telegram send error: %s", e)
            return False

    async def _send_telegram_alert(self, email_data: Dict[str, Any]) -> None:
        """Send a targeted Telegram alert for high-priority emails."""
        classification = email_data.get("classification", "general")
        emoji_map = {
            "hot_lead": "🔥",
            "showing_request": "🏠",
            "contract_update": "📝",
        }
        emoji = emoji_map.get(classification, "📧")

        lines = [
            f"{emoji} <b>{classification.replace('_', ' ').title()}</b>",
            f"<b>From:</b> {email_data.get('from_name', '')} &lt;{email_data.get('from_address', '')}&gt;",
            f"<b>Subject:</b> {email_data.get('subject', '')}",
        ]

        key_details = email_data.get("key_details", "")
        if key_details:
            lines.append(f"<b>Key Details:</b> {key_details}")

        preview = email_data.get("body_preview", "")[:200]
        if preview:
            lines.append(f"\n{preview}...")

        await self.send_telegram("\n".join(lines))

    # ------------------------------------------------------------------
    # Digest / stats
    # ------------------------------------------------------------------

    def get_email_digest(self) -> str:
        """Return a formatted summary of all processed emails."""
        if not self._processed_emails:
            return "No emails processed yet."

        lines = [f"<b>Email Triage Summary</b> ({len(self._processed_emails)} emails)\n"]

        # Group by classification
        by_cat: Dict[str, List[Dict[str, Any]]] = {}
        for e in self._processed_emails:
            cat = e.get("classification", "general")
            by_cat.setdefault(cat, []).append(e)

        priority_order = ["hot_lead", "warm_lead", "showing_request", "contract_update", "general", "spam"]
        for cat in priority_order:
            emails = by_cat.get(cat, [])
            if not emails:
                continue
            lines.append(f"<b>{cat.replace('_', ' ').title()}</b> ({len(emails)}):")
            for e in emails[:5]:
                lines.append(f"  - {e.get('from_name', 'Unknown')}: {e.get('subject', '(no subject)')}")
            if len(emails) > 5:
                lines.append(f"  ... and {len(emails) - 5} more")
            lines.append("")

        return "\n".join(lines)

    def get_stats(self) -> Dict[str, Any]:
        """Return email triage statistics."""
        total = sum(self._stats.values())
        return {
            "total_processed": total,
            "by_category": dict(self._stats),
            "emails": [
                {
                    "gmail_id": e.get("gmail_id"),
                    "from_name": e.get("from_name"),
                    "from_address": e.get("from_address"),
                    "subject": e.get("subject"),
                    "classification": e.get("classification"),
                    "priority": e.get("priority"),
                    "has_draft": bool(e.get("drafted_response")),
                }
                for e in self._processed_emails[-20:]  # Last 20
            ],
        }

    def reset(self) -> None:
        """Clear processed emails and stats."""
        self._processed_emails.clear()
        self._stats = {cat: 0 for cat in CATEGORIES}


# Module-level singleton
email_triage_service = EmailTriageService()
