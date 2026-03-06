"""
Morning Brief Service — generates and sends a daily morning summary via Telegram.

Pulls data from multiple tables (follow-ups, properties, scheduled tasks, pipeline)
and sends a clean, scannable Telegram message.
"""

import logging
import os
from datetime import datetime, timedelta

import httpx
from sqlalchemy import text

from app.database import SessionLocal

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TIMEZONE = "America/New_York"


async def _send_telegram(message: str) -> bool:
    """Send a message via Telegram Bot API using Markdown parse mode."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials not configured (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID)")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            logger.info("Morning brief sent via Telegram")
            return True
    except Exception as e:
        logger.error(f"Failed to send morning brief via Telegram: {e}")
        return False


def _get_eastern_now() -> datetime:
    """Get current datetime in America/New_York timezone."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo(TIMEZONE))
    except Exception:
        # Fallback: UTC - 5 (approximate)
        from datetime import timezone
        return datetime.now(timezone(timedelta(hours=-5)))


def _query_safe(db, sql: str, params: dict | None = None) -> list:
    """Execute a query safely, returning empty list on failure."""
    try:
        result = db.execute(text(sql), params or {})
        return [dict(row._mapping) for row in result]
    except Exception as e:
        logger.debug(f"Query skipped (table may not exist): {e}")
        return []


def _scalar_safe(db, sql: str, params: dict | None = None) -> int:
    """Execute a scalar query safely, returning 0 on failure."""
    try:
        result = db.execute(text(sql), params or {})
        row = result.fetchone()
        return row[0] if row else 0
    except Exception as e:
        logger.debug(f"Scalar query skipped: {e}")
        return 0


def generate_brief_text() -> str:
    """Generate the morning brief text by querying the database."""
    now = _get_eastern_now()
    today_str = now.strftime("%A, %B %d, %Y")
    today_date = now.strftime("%Y-%m-%d")

    # Calculate time boundaries
    yesterday = now - timedelta(hours=24)
    yesterday_str = yesterday.strftime("%Y-%m-%d %H:%M:%S")
    end_of_week = now + timedelta(days=(6 - now.weekday()))
    end_of_week_str = end_of_week.strftime("%Y-%m-%d")

    sections = []

    # Header
    greeting = "Good morning" if now.hour < 12 else "Good afternoon"
    sections.append(f"*{greeting}, Ed!*\n_{today_str}_\n")

    db = SessionLocal()
    try:
        # --- Follow-ups due today ---
        followups = _query_safe(db, """
            SELECT st.id, st.touch_type, st.message_content,
                   fs.name as sequence_name, fs.property_id
            FROM sequence_touches st
            JOIN follow_up_sequences fs ON st.sequence_id = fs.id
            WHERE st.status = 'scheduled'
              AND DATE(st.scheduled_date) = :today
            ORDER BY st.scheduled_date
            LIMIT 10
        """, {"today": today_date})

        if followups:
            lines = [f"*Follow-Ups Due Today* ({len(followups)})"]
            for fu in followups:
                seq_name = fu.get("sequence_name", "Unknown")
                touch_type = fu.get("touch_type", "follow-up")
                lines.append(f"  - {seq_name} ({touch_type})")
            sections.append("\n".join(lines))

        # --- New leads (last 24 hours) ---
        new_leads = _query_safe(db, """
            SELECT id, address, price, created_at
            FROM properties
            WHERE created_at >= :since
            ORDER BY created_at DESC
            LIMIT 5
        """, {"since": yesterday_str})

        new_leads_count = _scalar_safe(db, """
            SELECT COUNT(*) FROM properties WHERE created_at >= :since
        """, {"since": yesterday_str})

        if new_leads_count > 0:
            lines = [f"*New Leads (Last 24h)* ({new_leads_count})"]
            for lead in new_leads:
                addr = lead.get("address", "Unknown")
                price = lead.get("price")
                price_str = f" — ${price:,.0f}" if price else ""
                lines.append(f"  - {addr}{price_str}")
            if new_leads_count > 5:
                lines.append(f"  _...and {new_leads_count - 5} more_")
            sections.append("\n".join(lines))

        # --- Upcoming closings this week ---
        closings = _query_safe(db, """
            SELECT id, address, price, status
            FROM properties
            WHERE (LOWER(status) LIKE '%closing%' OR LOWER(status) LIKE '%contract%')
              AND DATE(updated_at) >= :today
              AND DATE(updated_at) <= :end_of_week
            ORDER BY updated_at
            LIMIT 5
        """, {"today": today_date, "end_of_week": end_of_week_str})

        # Also check by pipeline_stage
        closings2 = _query_safe(db, """
            SELECT id, address, price, pipeline_stage
            FROM properties
            WHERE (LOWER(pipeline_stage) LIKE '%closing%' OR LOWER(pipeline_stage) LIKE '%contract%')
            LIMIT 5
        """)

        all_closings = {c.get("id"): c for c in closings}
        for c in closings2:
            if c.get("id") not in all_closings:
                all_closings[c["id"]] = c

        if all_closings:
            lines = [f"*Closings & Under Contract* ({len(all_closings)})"]
            for c in list(all_closings.values())[:5]:
                addr = c.get("address", "Unknown")
                status = c.get("status") or c.get("pipeline_stage", "")
                price = c.get("price")
                price_str = f" — ${price:,.0f}" if price else ""
                lines.append(f"  - {addr}{price_str} [{status}]")
            sections.append("\n".join(lines))

        # --- Pipeline summary ---
        pipeline_by_status = _query_safe(db, """
            SELECT COALESCE(pipeline_stage, status, 'unknown') as stage,
                   COUNT(*) as cnt
            FROM properties
            GROUP BY COALESCE(pipeline_stage, status, 'unknown')
            ORDER BY cnt DESC
        """)

        if pipeline_by_status:
            total = sum(p["cnt"] for p in pipeline_by_status)
            lines = [f"*Pipeline Summary* ({total} total)"]
            for p in pipeline_by_status:
                stage = p["stage"] or "unset"
                lines.append(f"  - {stage}: {p['cnt']}")
            sections.append("\n".join(lines))

        # --- Active deals ---
        active_deals = _scalar_safe(db, """
            SELECT COUNT(*) FROM properties
            WHERE LOWER(COALESCE(status, '')) IN ('active', 'under_contract', 'negotiating', 'due_diligence')
               OR LOWER(COALESCE(pipeline_stage, '')) IN ('active', 'under_contract', 'negotiating', 'due_diligence')
        """)

        if active_deals > 0:
            sections.append(f"*Active Deals:* {active_deals}")

        # --- Scheduled tasks due today ---
        tasks = _query_safe(db, """
            SELECT id, title, action, status
            FROM scheduled_tasks
            WHERE DATE(scheduled_at) = :today
              AND status IN ('pending', 'running')
            ORDER BY scheduled_at
            LIMIT 10
        """, {"today": today_date})

        if tasks:
            lines = [f"*Scheduled Tasks Today* ({len(tasks)})"]
            for t in tasks:
                title = t.get("title") or t.get("action", "Task")
                lines.append(f"  - {title}")
            sections.append("\n".join(lines))

    except Exception as e:
        logger.error(f"Error generating morning brief: {e}")
        sections.append("_Some sections could not be loaded._")
    finally:
        db.close()

    # Motivational closer
    motivators = [
        "Let's close some deals today!",
        "Stay sharp, stay hungry.",
        "Every follow-up is a step closer to closing.",
        "Today's hustle is tomorrow's commission.",
        "Make it happen, Ed.",
        "Time to stack those deals.",
        "Fortune favors the persistent.",
    ]
    import hashlib
    day_hash = int(hashlib.md5(today_date.encode()).hexdigest(), 16)
    motivator = motivators[day_hash % len(motivators)]
    sections.append(f"\n_{motivator}_")

    return "\n\n".join(sections)


async def send_morning_brief() -> dict:
    """Generate and send the morning brief via Telegram."""
    brief_text = generate_brief_text()
    sent = await _send_telegram(brief_text)
    return {
        "brief": brief_text,
        "sent": sent,
        "channel": "telegram",
        "timestamp": _get_eastern_now().isoformat(),
    }
