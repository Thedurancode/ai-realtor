"""Discord bot — forwards messages to Claude agent."""

import asyncio
import logging
import os

import discord

from claude_agent import chat, clear_history

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger("claudebot.discord")

TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    logger.info("Discord bot logged in as %s", client.user)


@client.event
async def on_message(message: discord.Message):
    # Ignore own messages
    if message.author == client.user:
        return

    # Only respond to DMs or when mentioned
    is_dm = isinstance(message.channel, discord.DMChannel)
    is_mentioned = client.user in message.mentions if message.mentions else False

    if not is_dm and not is_mentioned:
        return

    text = message.content
    # Strip the bot mention from the text
    if is_mentioned:
        text = text.replace(f"<@{client.user.id}>", "").strip()

    if not text:
        return

    user_id = f"dc:{message.author.id}"

    # Handle commands
    if text.lower() == "/new":
        clear_history(user_id)
        await message.reply("Fresh start. What's up?")
        return

    # Show typing while processing
    async with message.channel.typing():
        try:
            response = await chat(user_id, text)
        except Exception as e:
            logger.error("Claude error: %s", e)
            response = f"Error: {e}"

    # Split long messages (Discord limit: 2000 chars)
    for i in range(0, len(response), 1900):
        chunk = response[i : i + 1900]
        await message.reply(chunk)


def run_discord():
    """Start the Discord bot."""
    if not TOKEN:
        logger.error("DISCORD_BOT_TOKEN not set")
        return
    logger.info("Discord bot starting...")
    client.run(TOKEN)


if __name__ == "__main__":
    run_discord()
