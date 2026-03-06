"""
ClaudeBot — Run both Telegram + Discord bots together with scheduled jobs.

Usage:
    python main.py              # Both bots + cron
    python main.py --telegram   # Telegram only
    python main.py --discord    # Discord only
    python main.py --no-cron    # Bots without scheduled jobs
"""

import asyncio
import logging
import os
import sys
import signal

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger("claudebot")


async def run_discord_async():
    """Run Discord bot in async mode."""
    import discord
    from claude_agent import chat, clear_history

    token = os.getenv("DISCORD_BOT_TOKEN", "")
    if not token:
        logger.warning("DISCORD_BOT_TOKEN not set, skipping Discord")
        return

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        logger.info("Discord bot logged in as %s", client.user)

    @client.event
    async def on_message(message: discord.Message):
        if message.author == client.user:
            return

        is_dm = isinstance(message.channel, discord.DMChannel)
        is_mentioned = client.user in message.mentions if message.mentions else False

        if not is_dm and not is_mentioned:
            return

        text = message.content
        if is_mentioned:
            text = text.replace(f"<@{client.user.id}>", "").strip()
        if not text:
            return

        user_id = f"dc:{message.author.id}"

        if text.lower() == "/new":
            clear_history(user_id)
            await message.reply("Fresh start. What's up?")
            return

        async with message.channel.typing():
            try:
                response = await chat(user_id, text)
            except Exception as e:
                logger.error("Claude error: %s", e)
                response = f"Error: {e}"

        for i in range(0, len(response), 1900):
            await message.reply(response[i : i + 1900])

    await client.start(token)


async def run_telegram_async():
    """Run Telegram bot in async mode."""
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    from claude_agent import chat, clear_history

    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN not set, skipping Telegram")
        return

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

    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message or not update.message.text:
            return
        text = update.message.text
        user_id = f"tg:{update.effective_user.id}"

        # Shortcut commands
        if text.lower().startswith("/digest"):
            text = "Give me today's daily digest"
        elif text.lower().startswith("/pipeline"):
            text = "Show me the pipeline summary"

        await update.message.chat.send_action("typing")
        try:
            response = await chat(user_id, text)
        except Exception as e:
            logger.error("Claude error: %s", e)
            response = f"Error: {e}"

        for i in range(0, len(response), 4000):
            await update.message.reply_text(response[i : i + 4000])

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("new", cmd_new))
    app.add_handler(CommandHandler("digest", handle))
    app.add_handler(CommandHandler("pipeline", handle))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
    logger.info("Telegram bot started")

    # Keep running
    while True:
        await asyncio.sleep(1)


async def run_cron_async():
    """Run scheduled jobs."""
    from cron_jobs import scheduler
    await scheduler()


async def main():
    args = set(sys.argv[1:])
    run_tg = "--telegram" in args or not args
    run_dc = "--discord" in args or not args
    run_cron = "--no-cron" not in args

    tasks = []
    if run_tg:
        tasks.append(asyncio.create_task(run_telegram_async()))
    if run_dc:
        tasks.append(asyncio.create_task(run_discord_async()))
    if run_cron:
        tasks.append(asyncio.create_task(run_cron_async()))

    if not tasks:
        logger.error("No bots to run. Set TELEGRAM_BOT_TOKEN and/or DISCORD_BOT_TOKEN")
        return

    logger.info("ClaudeBot starting — Telegram: %s, Discord: %s, Cron: %s", run_tg, run_dc, run_cron)

    try:
        await asyncio.gather(*tasks)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Shutting down...")


if __name__ == "__main__":
    asyncio.run(main())
