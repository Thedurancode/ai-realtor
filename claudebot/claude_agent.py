"""
Claude agent — handles conversation + tool calling loop.
Shared between Telegram and Discord bots.
"""

import os
from anthropic import AsyncAnthropic
from tools import TOOLS, execute_tool

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
MAX_TOKENS = 4096
MAX_ITERATIONS = 10

SYSTEM_PROMPT = """You are ClaudeBot, Ed Duran's AI real estate assistant powered by Claude.
You help manage properties, analyze deals, run research, send contracts, make calls, and more.

You have access to the full AI Realtor platform via tools. Use them to answer questions and take actions.

Guidelines:
- Be concise and direct. Ed knows his stuff.
- When asked about properties, deals, or pipeline — use the tools, don't guess.
- For anything the specific tools don't cover, use api_request to hit any endpoint.
- Format responses for chat (short paragraphs, bullet points).
- Always confirm before destructive actions (deleting, sending contracts, making calls).
"""

client = AsyncAnthropic()

# Per-user conversation history (chat_id -> messages)
conversations: dict[str, list[dict]] = {}
MAX_HISTORY = 40


async def chat(user_id: str, message: str) -> str:
    """Process a user message through Claude with tool use. Returns the final text response."""

    # Get or create conversation history
    if user_id not in conversations:
        conversations[user_id] = []

    history = conversations[user_id]
    history.append({"role": "user", "content": message})

    # Trim old messages
    if len(history) > MAX_HISTORY:
        history[:] = history[-MAX_HISTORY:]

    messages = list(history)

    # Agent loop — Claude may call tools multiple times
    for _ in range(MAX_ITERATIONS):
        response = await client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Collect text and tool_use blocks
        text_parts = []
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(block)

        if response.stop_reason == "tool_use" and tool_calls:
            # Add assistant message with all content blocks
            messages.append({"role": "assistant", "content": response.content})

            # Execute each tool and add results
            tool_results = []
            for tc in tool_calls:
                result = await execute_tool(tc.name, tc.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tc.id,
                    "content": result,
                })
            messages.append({"role": "user", "content": tool_results})
        else:
            # Final response — save to history and return
            final_text = "\n".join(text_parts) if text_parts else "Done."
            history.append({"role": "assistant", "content": final_text})
            return final_text

    return "I hit the tool call limit. Try breaking your request into smaller steps."


def clear_history(user_id: str) -> None:
    """Clear conversation history for a user."""
    conversations.pop(user_id, None)
