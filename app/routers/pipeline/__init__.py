"""Pipeline domain routers — activities, deal types, property recap, etc."""

from app.routers.pipeline.activities import router as activities_router
from app.routers.pipeline.property_recap import router as property_recap_router
from app.routers.pipeline.property_recap import _notes_router, _scoring_router
from app.routers.pipeline.webhooks import router as webhooks_router
from app.routers.pipeline.deal_types import router as deal_types_router
from app.routers.pipeline.pipeline import router as pipeline_router
from app.routers.pipeline.activity_timeline import router as activity_timeline_router

__all__ = [
    "activities_router", "property_recap_router", "webhooks_router",
    "deal_types_router", "pipeline_router", "activity_timeline_router",
    "_notes_router", "_scoring_router",
]
