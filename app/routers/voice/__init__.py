"""Voice / AI agent domain routers."""

from app.routers.voice.ai_agents import router as ai_agents_router
from app.routers.voice.elevenlabs import router as elevenlabs_router
from app.routers.voice.voice_campaigns import router as voice_campaigns_router
from app.routers.voice.voice_agent import router as voice_agent_router
from app.routers.voice.voice_agent import _memo_router
from app.routers.voice import telnyx

__all__ = [
    "ai_agents_router", "elevenlabs_router", "voice_campaigns_router",
    "voice_agent_router", "_memo_router", "telnyx",
]
