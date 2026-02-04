"""
Conversation Context Manager
Remembers recent actions for natural follow-up commands
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


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
