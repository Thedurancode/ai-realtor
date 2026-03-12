"""Video domain routers — rendering, chat, timeline, etc."""

from app.routers.video.videogen import router as videogen_router
from app.routers.video.renders import router as renders_router
from app.routers.video.video_chat import router as video_chat_router
from app.routers.video.pvc import router as pvc_router
from app.routers.video import timeline
from app.routers.video.shotstack_enhanced import router as shotstack_enhanced_router
from app.routers.video.shotstack_create import router as shotstack_create_router
from app.routers.video.agent_brand import router as agent_brand_router

__all__ = [
    "videogen_router", "renders_router", "video_chat_router",
    "pvc_router", "timeline", "shotstack_enhanced_router",
    "shotstack_create_router", "agent_brand_router",
]
