"""
Conversation Context Manager
Remembers recent actions for natural follow-up commands.

Supports:
- Fast in-memory context for active sessions
- Persistent graph sync helpers via MemoryGraphService
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.services.memory_graph import memory_graph_service


class ConversationContext:
    """
    Maintains conversation context for natural language follow-ups.

    Examples:
        "Create property at 123 Main St"
        → Remembers: last_property_id = 5

        "Skip trace this property"
        → Uses: last_property_id = 5
    """

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.context: Dict[str, Any] = {}
        self.last_updated = datetime.now()

    def set_last_property(self, property_id: int, address: str):
        """Remember the last property created or accessed"""
        self.context['last_property_id'] = property_id
        self.context['last_property_address'] = address
        self.last_updated = datetime.now()

    def get_last_property(self) -> Optional[int]:
        """Get the last property ID"""
        return self.context.get('last_property_id')

    def set_last_contact(self, contact_id: int, name: str):
        """Remember the last contact created or accessed"""
        self.context['last_contact_id'] = contact_id
        self.context['last_contact_name'] = name
        self.last_updated = datetime.now()

    def get_last_contact(self) -> Optional[int]:
        """Get the last contact ID"""
        return self.context.get('last_contact_id')

    def set_last_contract(self, contract_id: int, name: str):
        """Remember the last contract created or accessed"""
        self.context['last_contract_id'] = contract_id
        self.context['last_contract_name'] = name
        self.last_updated = datetime.now()

    def get_last_contract(self) -> Optional[int]:
        """Get the last contract ID"""
        return self.context.get('last_contract_id')

    def set_last_skip_trace(self, skip_trace_id: int, property_id: int):
        """Remember the last skip trace performed"""
        self.context['last_skip_trace_id'] = skip_trace_id
        self.context['last_skip_trace_property_id'] = property_id
        self.last_updated = datetime.now()

    def get_last_skip_trace(self) -> Optional[int]:
        """Get the last skip trace ID"""
        return self.context.get('last_skip_trace_id')

    def remember_objection(self, text: str, topic: Optional[str] = None):
        """Remember a user objection for future handling."""
        objections = self.context.setdefault("objections", [])
        objections.append(
            {
                "text": text,
                "topic": topic,
                "created_at": datetime.now().isoformat(),
            }
        )
        self.last_updated = datetime.now()

    def get_objections(self) -> List[Dict[str, Any]]:
        """Return recent objections."""
        return self.context.get("objections", [])

    def add_pending_promise(self, text: str, due_at: Optional[str] = None):
        """Track a commitment made by the assistant that needs follow-up."""
        promises = self.context.setdefault("pending_promises", [])
        promises.append(
            {
                "text": text,
                "due_at": due_at,
                "fulfilled": False,
                "created_at": datetime.now().isoformat(),
            }
        )
        self.last_updated = datetime.now()

    def fulfill_promise(self, promise_text: str) -> bool:
        """Mark a pending promise fulfilled."""
        promises = self.context.get("pending_promises", [])
        for promise in promises:
            if promise.get("text") == promise_text and not promise.get("fulfilled"):
                promise["fulfilled"] = True
                promise["fulfilled_at"] = datetime.now().isoformat()
                self.last_updated = datetime.now()
                return True
        return False

    def get_pending_promises(self) -> List[Dict[str, Any]]:
        """Get unresolved promises."""
        promises = self.context.get("pending_promises", [])
        return [p for p in promises if not p.get("fulfilled")]

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of current context"""
        return {
            "session_id": self.session_id,
            "last_property": {
                "id": self.context.get('last_property_id'),
                "address": self.context.get('last_property_address')
            },
            "last_contact": {
                "id": self.context.get('last_contact_id'),
                "name": self.context.get('last_contact_name')
            },
            "last_contract": {
                "id": self.context.get('last_contract_id'),
                "name": self.context.get('last_contract_name')
            },
            "last_skip_trace": {
                "id": self.context.get('last_skip_trace_id'),
                "property_id": self.context.get('last_skip_trace_property_id')
            },
            "objections": self.context.get("objections", []),
            "pending_promises": self.get_pending_promises(),
            "last_updated": self.last_updated.isoformat()
        }

    def is_stale(self, minutes: int = 30) -> bool:
        """Check if context is stale (older than X minutes)"""
        return datetime.now() - self.last_updated > timedelta(minutes=minutes)

    def clear(self):
        """Clear all context"""
        self.context = {}
        self.last_updated = datetime.now()


# Global context manager (in production, use session-based storage)
_contexts: Dict[str, ConversationContext] = {}


def get_context(session_id: str = "default") -> ConversationContext:
    """Get or create conversation context for a session"""
    if session_id not in _contexts:
        _contexts[session_id] = ConversationContext(session_id)
    return _contexts[session_id]


def hydrate_context_from_graph(db: Session, session_id: str = "default") -> ConversationContext:
    """
    Populate in-memory context from persistent graph state for this session.
    """
    context = get_context(session_id)
    summary = memory_graph_service.get_session_summary(db, session_id)
    state = summary.get("session_state", {})

    if state.get("last_property_id") is not None:
        context.context["last_property_id"] = state["last_property_id"]
    if state.get("last_property_address"):
        context.context["last_property_address"] = state["last_property_address"]
    if state.get("last_contact_id") is not None:
        context.context["last_contact_id"] = state["last_contact_id"]
    if state.get("last_contact_name"):
        context.context["last_contact_name"] = state["last_contact_name"]
    if state.get("last_contract_id") is not None:
        context.context["last_contract_id"] = state["last_contract_id"]
    if state.get("last_contract_name"):
        context.context["last_contract_name"] = state["last_contract_name"]

    context.last_updated = datetime.now()
    return context


def persist_context_to_graph(db: Session, session_id: str = "default") -> None:
    """
    Persist key in-memory context fields to the durable memory graph.
    """
    context = get_context(session_id)

    mapping = {
        "last_property_id": context.context.get("last_property_id"),
        "last_property_address": context.context.get("last_property_address"),
        "last_contact_id": context.context.get("last_contact_id"),
        "last_contact_name": context.context.get("last_contact_name"),
        "last_contract_id": context.context.get("last_contract_id"),
        "last_contract_name": context.context.get("last_contract_name"),
    }

    for key, value in mapping.items():
        if value is not None:
            memory_graph_service.remember_session_state(db, session_id, key, value)

    for objection in context.get_objections():
        memory_graph_service.remember_objection(
            db,
            session_id=session_id,
            text=objection.get("text", ""),
            topic=objection.get("topic"),
        )

    for promise in context.context.get("pending_promises", []):
        memory_graph_service.remember_promise(
            db,
            session_id=session_id,
            promise_text=promise.get("text", ""),
            due_at=promise.get("due_at"),
            fulfilled=promise.get("fulfilled", False),
        )

    db.flush()


def resolve_property_reference(
    property_ref: Optional[str],
    session_id: str = "default"
) -> Optional[int]:
    """
    Resolve property reference to ID.

    Args:
        property_ref: Can be:
            - "this" / "that" / "this property" → Use last property
            - "312 eisler" → Search by address
            - "2" / 2 → Direct ID
            - None → Use last property

    Returns:
        Property ID or None
    """
    context = get_context(session_id)

    # No reference provided - use last property
    if not property_ref:
        return context.get_last_property()

    # Context references
    if property_ref.lower() in ['this', 'that', 'this property', 'that property', 'it']:
        return context.get_last_property()

    # Try as direct ID
    try:
        return int(property_ref)
    except (ValueError, TypeError):
        pass

    # Address search would require database query
    # (implement in endpoint)
    return None


def resolve_contact_reference(
    contact_ref: Optional[str],
    session_id: str = "default"
) -> Optional[int]:
    """Resolve contact reference to ID"""
    context = get_context(session_id)

    if not contact_ref:
        return context.get_last_contact()

    if contact_ref.lower() in ['this', 'that', 'this contact', 'them', 'him', 'her']:
        return context.get_last_contact()

    try:
        return int(contact_ref)
    except (ValueError, TypeError):
        pass

    return None
