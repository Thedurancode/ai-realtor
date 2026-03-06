"""
ClaudeBot scheduled jobs + heartbeat — runs on a loop, sends messages to Telegram/Discord.

Usage:
    python cron_jobs.py
"""

import asyncio
import os
import logging
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from claude_agent import chat

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger("claudebot.cron")

# Your Telegram chat ID (get it by messaging @userinfobot on Telegram)
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
HEARTBEAT_FILE = Path(__file__).parent / "HEARTBEAT.md"
HEARTBEAT_INTERVAL = 30 * 60  # 30 minutes


async def send_telegram(text: str) -> None:
    """Send a message to your Telegram."""
    if not TELEGRAM_CHAT_ID or not TELEGRAM_TOKEN:
        logger.warning("TELEGRAM_CHAT_ID or TELEGRAM_BOT_TOKEN not set")
        return

    import httpx
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        await client.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text[:4000]})


# --- Define your scheduled jobs ---

async def morning_digest():
    """7:30 AM ET — Daily digest + pipeline summary."""
    logger.info("Running morning digest...")
    response = await chat("cron:digest",
        "Give me today's morning briefing: daily digest, pipeline summary, "
        "any properties that need attention, and pending follow-ups. Keep it concise."
    )
    await send_telegram(f"☀️ Morning Briefing\n\n{response}")


async def evening_recap():
    """6:00 PM ET — End of day recap."""
    logger.info("Running evening recap...")
    response = await chat("cron:recap",
        "End of day recap: what happened today? Any new offers, contract updates, "
        "or calls that came in? What should I focus on tomorrow?"
    )
    await send_telegram(f"🌙 Evening Recap\n\n{response}")


async def market_scan():
    """Every 4 hours — Check for market opportunities."""
    logger.info("Running market scan...")
    response = await chat("cron:market",
        "Quick market scan: any new watchlist matches, price drops, "
        "or properties that just hit the market matching my criteria?"
    )
    # Only send if there's something interesting
    if "no new" not in response.lower() and "nothing" not in response.lower():
        await send_telegram(f"📊 Market Alert\n\n{response}")


# --- Heartbeat ---

async def heartbeat():
    """Every 30 min — read HEARTBEAT.md, act on active tasks, update the file."""
    if not HEARTBEAT_FILE.exists():
        return

    content = HEARTBEAT_FILE.read_text()

    # Extract active tasks section
    if "## Active Tasks" not in content:
        return
    active_section = content.split("## Active Tasks")[1]
    if "## Completed" in active_section:
        active_section = active_section.split("## Completed")[0]

    # Strip comments and empty lines
    tasks = [
        line.strip() for line in active_section.strip().splitlines()
        if line.strip() and not line.strip().startswith("<!--")
    ]

    if not tasks:
        logger.debug("Heartbeat: no active tasks")
        return

    logger.info("Heartbeat: %d active tasks found", len(tasks))
    task_list = "\n".join(tasks)

    response = await chat("heartbeat",
        f"You have active heartbeat tasks to check on. Review each one, "
        f"use your tools to check status, and report back. "
        f"If a task is done, say so clearly.\n\n"
        f"Active tasks:\n{task_list}"
    )

    await send_telegram(f"💓 Heartbeat Check\n\n{response}")

    # Auto-move completed tasks
    completed_markers = ["done", "completed", "resolved", "no longer", "finished"]
    response_lower = response.lower()

    remaining = []
    newly_completed = []
    for task in tasks:
        # Check if Claude's response indicates this task is done
        task_words = task.lower().replace("-", "").replace("*", "").strip()
        if any(marker in response_lower for marker in completed_markers) and \
           any(word in response_lower for word in task_words.split()[:3]):
            newly_completed.append(task)
        else:
            remaining.append(task)

    if newly_completed:
        # Rewrite HEARTBEAT.md
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        completed_section = content.split("## Completed")[1] if "## Completed" in content else ""

        new_completed = "\n".join(f"{t} ✅ ({now})" for t in newly_completed)
        new_active = "\n".join(remaining) if remaining else "<!-- No active tasks -->"

        new_content = (
            "# Heartbeat Tasks\n\n"
            "Checked every 30 minutes. Add tasks below — ClaudeBot will act on them automatically.\n\n"
            "## Active Tasks\n\n"
            f"{new_active}\n\n"
            "## Completed\n\n"
            f"{new_completed}\n{completed_section}"
        )
        HEARTBEAT_FILE.write_text(new_content)
        logger.info("Heartbeat: moved %d tasks to completed", len(newly_completed))


# --- Scheduler ---

SCHEDULE = [
    # (hour, minute, job_func)
    (7, 30, morning_digest),
    (18, 0, evening_recap),
    # Market scan every 4 hours during business hours
    (9, 0, market_scan),
    (13, 0, market_scan),
    (17, 0, market_scan),
]


async def scheduler():
    """Runs cron jobs on schedule + heartbeat every 30 min."""
    ran_today: dict[str, str] = {}
    last_heartbeat = 0

    logger.info("Scheduler started with %d cron jobs + heartbeat (every %ds)", len(SCHEDULE), HEARTBEAT_INTERVAL)
    for hour, minute, func in SCHEDULE:
        logger.info("  %02d:%02d → %s", hour, minute, func.__name__)

    while True:
        now = datetime.now()

        # Cron jobs
        for hour, minute, func in SCHEDULE:
            key = f"{hour}:{minute}:{func.__name__}"
            today = now.strftime("%Y-%m-%d")

            if now.hour == hour and now.minute == minute and ran_today.get(key) != today:
                ran_today[key] = today
                try:
                    await func()
                except Exception as e:
                    logger.error("Job %s failed: %s", func.__name__, e)

        # Heartbeat
        elapsed = asyncio.get_event_loop().time() - last_heartbeat
        if elapsed >= HEARTBEAT_INTERVAL:
            last_heartbeat = asyncio.get_event_loop().time()
            try:
                await heartbeat()
            except Exception as e:
                logger.error("Heartbeat failed: %s", e)

        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(scheduler())
