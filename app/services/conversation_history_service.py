"""Service for managing conversation history."""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.conversation_history import ConversationHistory


def log_conversation(
    db: Session,
    session_id: str,
    tool_name: str,
    input_summary: str,
    output_summary: str,
    input_data: Optional[dict] = None,
    output_data: Optional[dict] = None,
    success: bool = True,
    duration_ms: Optional[int] = None,
    property_id: Optional[int] = None,
) -> ConversationHistory:
    """Log a conversation/tool call to history."""
    entry = ConversationHistory(
        session_id=session_id,
        property_id=property_id,
        tool_name=tool_name,
        input_summary=input_summary,
        output_summary=output_summary,
        input_data=input_data,
        output_data=output_data,
        success=1 if success else 0,
        duration_ms=duration_ms,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_conversation_history(
    db: Session,
    session_id: str,
    limit: int = 10,
    hours_ago: Optional[int] = None,
    property_id: Optional[int] = None,
) -> list[ConversationHistory]:
    """Get recent conversation history for a session, optionally filtered by property."""
    query = db.query(ConversationHistory).filter(
        ConversationHistory.session_id == session_id
    )

    if property_id:
        query = query.filter(ConversationHistory.property_id == property_id)

    if hours_ago:
        cutoff = datetime.utcnow() - timedelta(hours=hours_ago)
        query = query.filter(ConversationHistory.created_at >= cutoff)

    return query.order_by(desc(ConversationHistory.created_at)).limit(limit).all()


def get_property_history(
    db: Session,
    property_id: int,
    limit: int = 50,
) -> list[ConversationHistory]:
    """Get all conversation history for a specific property across all sessions."""
    return (
        db.query(ConversationHistory)
        .filter(ConversationHistory.property_id == property_id)
        .order_by(desc(ConversationHistory.created_at))
        .limit(limit)
        .all()
    )


def format_history_for_voice(history: list[ConversationHistory]) -> str:
    """Format conversation history for voice/text output."""
    if not history:
        return "No recent conversation history found."

    lines = ["Here's what we discussed recently:"]
    now = datetime.utcnow()

    for entry in reversed(history):  # Show oldest first
        time_ago = _time_ago(entry.created_at, now)
        status = "" if entry.success else " (failed)"
        lines.append(f"- [{time_ago}] {entry.output_summary}{status}")

    return "\n".join(lines)


def format_property_history_for_voice(history: list[ConversationHistory]) -> str:
    """Format property-specific history as a voice-friendly timeline."""
    if not history:
        return "No actions recorded for this property."

    lines = [f"{len(history)} action{'s' if len(history) != 1 else ''} on this property:"]
    now = datetime.utcnow()

    for entry in reversed(history):  # Show oldest first
        time_ago = _time_ago(entry.created_at, now)
        status = "" if entry.success else " (failed)"
        lines.append(f"- [{time_ago}] {entry.output_summary}{status}")

    return "\n".join(lines)


def _time_ago(dt: datetime, now: datetime) -> str:
    """Human-readable time delta."""
    entry_time = dt.replace(tzinfo=None) if dt.tzinfo else dt
    delta = now - entry_time

    if delta.total_seconds() < 60:
        return "just now"
    if delta.total_seconds() < 3600:
        mins = int(delta.total_seconds() / 60)
        return f"{mins} min ago"
    if delta.total_seconds() < 86400:
        hours = int(delta.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    days = int(delta.total_seconds() / 86400)
    return f"{days} day{'s' if days > 1 else ''} ago"


def get_last_topic(db: Session, session_id: str) -> Optional[str]:
    """Get the last thing discussed."""
    entry = db.query(ConversationHistory).filter(
        ConversationHistory.session_id == session_id
    ).order_by(desc(ConversationHistory.created_at)).first()

    if entry:
        return entry.output_summary
    return None


def clear_history(db: Session, session_id: str) -> int:
    """Clear conversation history for a session. Returns count deleted."""
    count = db.query(ConversationHistory).filter(
        ConversationHistory.session_id == session_id
    ).delete()
    db.commit()
    return count
