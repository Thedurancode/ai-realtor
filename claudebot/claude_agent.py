"""
Claude agent — routes messages through Claude Code CLI for full MCP tool access.
Shared between Telegram and Discord bots.
"""

import asyncio
import os
import json
import logging

logger = logging.getLogger("claudebot.agent")

PROJECT_DIR = os.getenv("PROJECT_DIR", "/root/Documents/GitHub/ai-realtor")
CLAUDE_BIN = os.getenv("CLAUDE_BIN", "claude")

# Per-user conversation history (chat_id -> messages)
conversations: dict[str, list[str]] = {}
MAX_HISTORY = 20


async def chat(user_id: str, message: str) -> str:
    """Process a user message through Claude Code CLI with full MCP tools."""

    # Build context from recent history
    if user_id not in conversations:
        conversations[user_id] = []

    history = conversations[user_id]
    history.append(f"User: {message}")

    if len(history) > MAX_HISTORY:
        history[:] = history[-MAX_HISTORY:]

    # Build the prompt with recent context
    context_lines = history[-10:]  # Last 10 exchanges for context
    prompt = "\n".join(context_lines)

    try:
        proc = await asyncio.create_subprocess_exec(
            CLAUDE_BIN, "-p", "--dangerously-skip-permissions",
            "--output-format", "text",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=PROJECT_DIR,
            env={
                **os.environ,
                "CLAUDE_CODE_ENTRYPOINT": "cli",
            },
        )

        stdout, stderr = await asyncio.wait_for(
            proc.communicate(input=prompt.encode()),
            timeout=120,
        )

        response = stdout.decode().strip()

        if not response and stderr:
            err = stderr.decode().strip()
            logger.error("Claude CLI stderr: %s", err[:500])
            response = f"Error running Claude: {err[:200]}"

        if not response:
            response = "No response from Claude."

    except asyncio.TimeoutError:
        response = "Request timed out (120s). Try a simpler question."
        logger.error("Claude CLI timed out for user %s", user_id)
    except FileNotFoundError:
        response = "Claude CLI not found. Make sure it's installed (npm install -g @anthropic-ai/claude-code)."
        logger.error("Claude CLI binary not found at: %s", CLAUDE_BIN)
    except Exception as e:
        response = f"Error: {e}"
        logger.error("Claude CLI error: %s", e)

    history.append(f"Assistant: {response[:500]}")
    return response


def clear_history(user_id: str) -> None:
    """Clear conversation history for a user."""
    conversations.pop(user_id, None)
