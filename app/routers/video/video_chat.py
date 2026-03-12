"""AI Video Chat — Vibe-editing endpoint.

Streams Claude responses that modify Shotstack timeline JSON based on
natural language instructions from the user.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import httpx
import json

from app.config import settings

router = APIRouter(prefix="/video-chat", tags=["video-chat"])

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "anthropic/claude-sonnet-4"

SYSTEM_PROMPT = """You are a Shotstack video timeline editor. The user describes changes to their video and you return the COMPLETE modified Shotstack Edit JSON.

Rules:
- Return ONLY valid JSON (no markdown, no explanation, no code fences)
- Keep all existing clips/tracks unless the user asks to remove them
- Shotstack clip structure: { asset: { type, src/html/text, width, height }, start, length, transition, position, scale, opacity, fit }
- Asset types: video, image, html, audio, title
- Transitions: fade, reveal, wipeLeft, wipeRight, slideLeft, slideRight, slideUp, slideDown, zoom
- Positions: center, top, topRight, right, bottomRight, bottom, bottomLeft, left, topLeft
- For text changes, modify the HTML inside the html asset
- For timing changes, adjust start/length values
- Always return the full timeline, not just the changed parts
- The output must be parseable by JSON.parse() with no surrounding text"""


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str


class VideoChatRequest(BaseModel):
    timeline: Dict[str, Any] = Field(..., description="Current Shotstack Edit JSON")
    message: str = Field(..., description="User's editing instruction")
    history: Optional[List[ChatMessage]] = Field(default=None, description="Prior chat messages")


@router.post("/edit")
async def video_chat_edit(request: VideoChatRequest):
    """Stream an AI-edited Shotstack timeline JSON back to the client via SSE."""
    api_key = settings.openrouter_api_key
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenRouter API key not configured")

    # Build message list
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add conversation history
    if request.history:
        for msg in request.history:
            messages.append({"role": msg.role, "content": msg.content})

    # Current user message includes the timeline context
    user_content = (
        f"Current timeline JSON:\n```json\n{json.dumps(request.timeline, indent=2)}\n```\n\n"
        f"User request: {request.message}"
    )
    messages.append({"role": "user", "content": user_content})

    async def generate():
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                async with client.stream(
                    "POST",
                    OPENROUTER_URL,
                    json={
                        "model": MODEL,
                        "messages": messages,
                        "stream": True,
                        "max_tokens": 16000,
                        "temperature": 0.3,
                    },
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "HTTP-Referer": "https://ai-realtor.com",
                        "X-Title": "AI Realtor Video Editor",
                        "Content-Type": "application/json",
                    },
                ) as response:
                    if response.status_code != 200:
                        body = await response.aread()
                        yield f"data: {json.dumps({'error': f'OpenRouter error {response.status_code}: {body.decode()}'})}\n\n"
                        yield "data: [DONE]\n\n"
                        return

                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        payload = line[6:]
                        if payload.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(payload)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield f"data: {json.dumps({'content': content})}\n\n"
                        except json.JSONDecodeError:
                            continue

            except httpx.ReadTimeout:
                yield f"data: {json.dumps({'error': 'Request timed out'})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
