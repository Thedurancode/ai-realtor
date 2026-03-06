"""Telegram bot — forwards messages to Claude agent."""

import asyncio
import logging
import os

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from claude_agent import chat, clear_history

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger("claudebot.telegram")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hey! I'm ClaudeBot — your AI real estate assistant.\n"
        "Send me anything and I'll use the full AI Realtor platform to help.\n\n"
        "/new — Start fresh conversation\n"
        "/digest — Get today's digest\n"
        "/pipeline — Pipeline summary"
    )


async def cmd_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    clear_history(f"tg:{update.effective_user.id}")
    await update.message.reply_text("Fresh start. What's up?")


async def cmd_digest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _handle(update, "Give me today's daily digest")


async def cmd_pipeline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _handle(update, "Show me the pipeline summary")


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    await _handle(update, update.message.text)


async def _handle(update: Update, text: str) -> None:
    user_id = f"tg:{update.effective_user.id}"

    # Send typing indicator
    await update.message.chat.send_action("typing")

    try:
        response = await chat(user_id, text)
    except Exception as e:
        logger.error("Claude error: %s", e)
        response = f"Error: {e}"

    # Split long messages (Telegram limit: 4096 chars)
    for i in range(0, len(response), 4000):
        chunk = response[i : i + 4000]
        await update.message.reply_text(chunk)


def run_telegram():
    """Start the Telegram bot."""
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set")
        return

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("new", cmd_new))
    app.add_handler(CommandHandler("digest", cmd_digest))
    app.add_handler(CommandHandler("pipeline", cmd_pipeline))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    logger.info("Telegram bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    run_telegram()
