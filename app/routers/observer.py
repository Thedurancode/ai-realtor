"""Observer Pattern API router.

Provides endpoints for managing event bus subscriptions and viewing event history.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.services.observer import event_bus, EventType


router = APIRouter(prefix="/observer", tags=["Observer Pattern"])


# Pydantic models
class EventPublishRequest(BaseModel):
    """Request to publish an event."""
    event_type: str
    data: Dict[str, Any]


@router.get("/stats")
async def get_observer_stats():
    """Get statistics about event bus subscribers and history."""
    stats = event_bus.get_subscriber_stats()

    return {
        "enabled": event_bus.enabled,
        "total_subscribers": stats["total_subscribers"],
        "subscribers_by_type": stats["subscribers_by_type"],
        "publish_count": event_bus.publish_count,
        "history_size": len(event_bus.event_history),
        "max_history_size": event_bus.max_history_size,
        "top_subscribers": stats["top_subscribers"]
    }


@router.get("/history")
async def get_event_history(
    event_type: Optional[str] = None,
    limit: int = 100
):
    """Get event history.

    Optionally filter by event type.
    """
    # Convert string to EventType if provided
    event_type_enum = None
    if event_type:
        try:
            event_type_enum = EventType(event_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {event_type}")

    history = event_bus.get_history(event_type=event_type_enum, limit=limit)

    return {
        "total_events": len(history),
        "events": history
    }


@router.delete("/history")
async def clear_event_history():
    """Clear event history."""
    event_bus.clear_history()

    return {
        "status": "cleared"
    }


@router.post("/enable")
async def enable_event_bus():
    """Enable event publishing."""
    event_bus.enable()

    return {
        "status": "enabled",
        "enabled": event_bus.enabled
    }


@router.post("/disable")
async def disable_event_bus():
    """Disable event publishing."""
    event_bus.disable()

    return {
        "status": "disabled",
        "enabled": event_bus.enabled
    }


@router.get("/event-types")
async def get_event_types():
    """Get all available event types."""
    return {
        "event_types": [e.value for e in EventType]
    }


@router.get("/subscribers")
async def get_subscribers():
    """Get all subscribers with their stats."""
    stats = event_bus.get_subscriber_stats()

    subscribers = []
    for event_type, subs in event_bus.subscribers.items():
        for sub in subs:
            subscribers.append({
                "name": sub.name,
                "event_type": event_type.value,
                "call_count": sub.call_count,
                "last_called": sub.last_called.isoformat() if sub.last_called else None,
                "has_filter": sub.filter_func is not None
            })

    return {
        "total_subscribers": len(subscribers),
        "subscribers": subscribers
    }
