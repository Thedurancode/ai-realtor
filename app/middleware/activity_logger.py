"""
Activity logging middleware to capture all API requests and MCP tool calls
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import json
from typing import Callable
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.activity_event import ActivityEvent, ActivityEventType, ActivityEventStatus


class ActivityLoggerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all API requests as activity events
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for health checks, static files, and WebSocket connections
        if request.url.path in ["/health", "/", "/docs", "/openapi.json"] or request.url.path.startswith("/ws"):
            return await call_next(request)

        # Record start time
        start_time = time.time()

        # Extract request information
        method = request.method
        path = request.url.path
        user_source = request.headers.get("User-Agent", "Unknown")

        # Determine tool name from path
        tool_name = f"{method} {path}"

        # Process the request
        response = await call_next(request)

        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)

        # Determine status based on response status code
        if response.status_code < 400:
            status = ActivityEventStatus.SUCCESS
        else:
            status = ActivityEventStatus.ERROR

        # Create activity event in database
        try:
            db = SessionLocal()
            activity_event = ActivityEvent(
                tool_name=tool_name,
                user_source=user_source,
                event_type=ActivityEventType.TOOL_CALL,
                status=status,
                duration_ms=duration_ms,
                data=json.dumps({
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "query_params": dict(request.query_params)
                })
            )
            db.add(activity_event)
            db.commit()
            db.close()
        except Exception as e:
            print(f"Error logging activity: {e}")

        return response


def log_mcp_tool_call(
    tool_name: str,
    user_source: str = "MCP Server",
    metadata: dict = None,
    db: Session = None
) -> ActivityEvent:
    """
    Helper function to log MCP tool calls

    Args:
        tool_name: Name of the MCP tool being called
        user_source: Source of the call (e.g., "Claude Desktop")
        metadata: Additional metadata about the tool call
        db: Database session (optional, will create new if not provided)

    Returns:
        The created ActivityEvent
    """
    should_close_db = False
    if db is None:
        db = SessionLocal()
        should_close_db = True

    try:
        activity_event = ActivityEvent(
            tool_name=tool_name,
            user_source=user_source,
            event_type=ActivityEventType.TOOL_CALL,
            status=ActivityEventStatus.PENDING,
            data=json.dumps(metadata) if metadata else None
        )
        db.add(activity_event)
        db.commit()
        db.refresh(activity_event)
        return activity_event
    finally:
        if should_close_db:
            db.close()


def update_mcp_tool_result(
    activity_event_id: int,
    status: ActivityEventStatus,
    duration_ms: int,
    error_message: str = None,
    db: Session = None
) -> ActivityEvent:
    """
    Update an MCP tool call with its result

    Args:
        activity_event_id: ID of the activity event to update
        status: Final status (SUCCESS or ERROR)
        duration_ms: Duration of the tool execution in milliseconds
        error_message: Error message if status is ERROR
        db: Database session (optional, will create new if not provided)

    Returns:
        The updated ActivityEvent
    """
    should_close_db = False
    if db is None:
        db = SessionLocal()
        should_close_db = True

    try:
        activity_event = db.query(ActivityEvent).filter(ActivityEvent.id == activity_event_id).first()
        if activity_event:
            activity_event.status = status
            activity_event.duration_ms = duration_ms
            if error_message:
                activity_event.error_message = error_message
            db.commit()
            db.refresh(activity_event)
        return activity_event
    finally:
        if should_close_db:
            db.close()
