"""Observer Pattern for Event Tracking.

Inspired by ZeroClaw's observer pattern, this module provides a centralized
event bus for tracking property events across the entire platform.

Subscribers can register to receive events for:
- Property creation/update/deletion
- Contract lifecycle events
- Contact additions
- Enrichment completions
- Skip trace results
- Phone calls
- Workflow executions

Usage:
    from app.services.observer import event_bus

    # Subscribe to events
    def handle_property_created(event: PropertyEvent):
        print(f"Property {event.property_id} created!")

    event_bus.subscribe("property.created", handle_property_created)

    # Publish events
    event_bus.publish("property.created", PropertyEvent(
        property_id=5,
        agent_id=2,
        timestamp=datetime.now()
    ))
"""

from datetime import datetime
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json


class EventType(str, Enum):
    """Types of events that can be published."""

    # Property events
    PROPERTY_CREATED = "property.created"
    PROPERTY_UPDATED = "property.updated"
    PROPERTY_DELETED = "property.deleted"
    PROPERTY_ENRICHED = "property.enriched"
    PROPERTY_SKIP_TRACED = "property.skip_traced"

    # Contract events
    CONTRACT_CREATED = "contract.created"
    CONTRACT_SENT = "contract.sent"
    CONTRACT_COMPLETED = "contract.completed"
    CONTRACT_CANCELLED = "contract.cancelled"

    # Contact events
    CONTACT_ADDED = "contact.added"
    CONTACT_UPDATED = "contact.updated"

    # Note events
    NOTE_ADDED = "note.added"

    # Phone call events
    PHONE_CALL_STARTED = "phone_call.started"
    PHONE_CALL_COMPLETED = "phone_call.completed"
    PHONE_CALL_FAILED = "phone_call.failed"

    # Workflow events
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"

    # Agent events
    AGENT_ONBOARDED = "agent.onboarded"
    AGENT_LOGIN = "agent.login"
    AGENT_LOGOUT = "agent.logout"


@dataclass
class PropertyEvent:
    """Base event data class for property-related events."""
    property_id: int
    agent_id: int
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContractEvent:
    """Event data for contract-related events."""
    contract_id: int
    property_id: int
    agent_id: int
    status: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContactEvent:
    """Event data for contact-related events."""
    contact_id: int
    property_id: int
    agent_id: int
    role: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PhoneCallEvent:
    """Event data for phone call events."""
    call_id: str
    property_id: Optional[int]
    contact_id: Optional[int]
    agent_id: int
    phone_number: str
    status: str
    duration_seconds: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowEvent:
    """Event data for workflow events."""
    workflow_id: str
    workflow_name: str
    property_id: Optional[int]
    agent_id: int
    status: str
    steps_completed: int = 0
    total_steps: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class EventSubscriber:
    """A subscriber to event bus events."""

    def __init__(
        self,
        event_type: EventType,
        handler: Callable,
        name: Optional[str] = None,
        filter_func: Optional[Callable] = None
    ):
        """Initialize an event subscriber.

        Args:
            event_type: Type of event to subscribe to
            handler: Callback function to handle events
            name: Optional name for the subscriber
            filter_func: Optional filter function (returns True to handle event)
        """
        self.event_type = event_type
        self.handler = handler
        self.name = name or handler.__name__
        self.filter_func = filter_func
        self.call_count = 0
        self.last_called: Optional[datetime] = None

    async def handle(self, event: Any) -> None:
        """Handle an event if it passes the filter.

        Args:
            event: Event data
        """
        # Check filter
        if self.filter_func and not self.filter_func(event):
            return

        # Call handler
        await self.handler(event)

        # Update stats
        self.call_count += 1
        self.last_called = datetime.now()


class EventBus:
    """Central event bus for publishing and subscribing to events."""

    def __init__(self):
        """Initialize event bus."""
        self.subscribers: Dict[EventType, List[EventSubscriber]] = {}
        self.event_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000
        self.publish_count = 0
        self.enabled = True

    def subscribe(
        self,
        event_type: EventType,
        handler: Callable,
        name: Optional[str] = None,
        filter_func: Optional[Callable] = None
    ) -> EventSubscriber:
        """Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Callback function to handle events
            name: Optional name for the subscriber
            filter_func: Optional filter function (receives event, returns bool)

        Returns:
            EventSubscriber instance

        Example:
            def handle_created(event: PropertyEvent):
                print(f"Property {event.property_id} created!")

            event_bus.subscribe(
                EventType.PROPERTY_CREATED,
                handle_created,
                name="property_created_logger"
            )
        """
        subscriber = EventSubscriber(
            event_type=event_type,
            handler=handler,
            name=name,
            filter_func=filter_func
        )

        if event_type not in self.subscribers:
            self.subscribers[event_type] = []

        self.subscribers[event_type].append(subscriber)

        return subscriber

    def unsubscribe(self, event_type: EventType, handler: Callable) -> bool:
        """Unsubscribe a handler from an event type.

        Args:
            event_type: Type of event to unsubscribe from
            handler: Handler function to remove

        Returns:
            True if unsubscribed, False if not found
        """
        if event_type not in self.subscribers:
            return False

        # Find and remove subscriber
        for i, subscriber in enumerate(self.subscribers[event_type]):
            if subscriber.handler == handler:
                self.subscribers[event_type].pop(i)
                return True

        return False

    async def publish(self, event_type: EventType, event: Any) -> None:
        """Publish an event to all subscribers.

        Args:
            event_type: Type of event to publish
            event: Event data (PropertyEvent, ContractEvent, etc.)

        Example:
            await event_bus.publish(
                EventType.PROPERTY_CREATED,
                PropertyEvent(property_id=5, agent_id=2)
            )
        """
        if not self.enabled:
            return

        # Add to history
        self._add_to_history(event_type, event)

        # Update publish count
        self.publish_count += 1

        # Notify subscribers
        if event_type in self.subscribers:
            for subscriber in self.subscribers[event_type]:
                try:
                    await subscriber.handle(event)
                except Exception as e:
                    # Log error but don't stop other subscribers
                    print(f"Error in subscriber {subscriber.name}: {e}")

    def _add_to_history(self, event_type: EventType, event: Any) -> None:
        """Add event to history.

        Args:
            event_type: Type of event
            event: Event data
        """
        # Serialize event to dict
        event_dict = {
            "event_type": event_type.value,
            "timestamp": datetime.now().isoformat(),
            "data": self._serialize_event(event)
        }

        # Add to history
        self.event_history.append(event_dict)

        # Trim history if needed
        if len(self.event_history) > self.max_history_size:
            self.event_history = self.event_history[-self.max_history_size:]

    def _serialize_event(self, event: Any) -> Dict[str, Any]:
        """Serialize event to dictionary.

        Args:
            event: Event object

        Returns:
            Dictionary representation
        """
        if hasattr(event, "__dataclass_fields__"):
            # Dataclass
            return {
                k: str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
                for k, v in event.__dict__.items()
            }
        elif isinstance(event, dict):
            return event
        else:
            return {"value": str(event)}

    def get_history(
        self,
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get event history.

        Args:
            event_type: Optional event type to filter by
            limit: Maximum number of events to return

        Returns:
            List of event dictionaries
        """
        history = self.event_history

        # Filter by event type
        if event_type:
            history = [
                e for e in history
                if e["event_type"] == event_type.value
            ]

        # Sort by timestamp (newest first) and limit
        history = sorted(history, key=lambda x: x["timestamp"], reverse=True)[:limit]

        return history

    def get_subscriber_stats(self) -> Dict[str, Any]:
        """Get statistics about subscribers.

        Returns:
            Dictionary with subscriber stats
        """
        stats = {
            "total_subscribers": sum(len(subs) for subs in self.subscribers.values()),
            "subscribers_by_type": {},
            "top_subscribers": []
        }

        # Count by type
        for event_type, subscribers in self.subscribers.items():
            stats["subscribers_by_type"][event_type.value] = len(subscribers)

        # Find top subscribers by call count
        all_subscribers = []
        for subscribers in self.subscribers.values():
            all_subscribers.extend(subscribers)

        stats["top_subscribers"] = [
            {
                "name": sub.name,
                "event_type": sub.event_type.value,
                "call_count": sub.call_count,
                "last_called": sub.last_called.isoformat() if sub.last_called else None
            }
            for sub in sorted(all_subscribers, key=lambda x: x.call_count, reverse=True)[:10]
        ]

        return stats

    def clear_history(self) -> None:
        """Clear event history."""
        self.event_history = []

    def enable(self) -> None:
        """Enable event publishing."""
        self.enabled = True

    def disable(self) -> None:
        """Disable event publishing."""
        self.enabled = False


# Global singleton instance
event_bus = EventBus()


# Convenience functions for common events
async def publish_property_created(property_id: int, agent_id: int, **metadata):
    """Publish property created event."""
    await event_bus.publish(
        EventType.PROPERTY_CREATED,
        PropertyEvent(property_id=property_id, agent_id=agent_id, metadata=metadata)
    )


async def publish_property_updated(property_id: int, agent_id: int, **metadata):
    """Publish property updated event."""
    await event_bus.publish(
        EventType.PROPERTY_UPDATED,
        PropertyEvent(property_id=property_id, agent_id=agent_id, metadata=metadata)
    )


async def publish_property_deleted(property_id: int, agent_id: int, **metadata):
    """Publish property deleted event."""
    await event_bus.publish(
        EventType.PROPERTY_DELETED,
        PropertyEvent(property_id=property_id, agent_id=agent_id, metadata=metadata)
    )


async def publish_property_enriched(property_id: int, agent_id: int, **metadata):
    """Publish property enriched event."""
    await event_bus.publish(
        EventType.PROPERTY_ENRICHED,
        PropertyEvent(property_id=property_id, agent_id=agent_id, metadata=metadata)
    )


async def publish_contract_created(
    contract_id: int,
    property_id: int,
    agent_id: int,
    status: str,
    **metadata
):
    """Publish contract created event."""
    await event_bus.publish(
        EventType.CONTRACT_CREATED,
        ContractEvent(
            contract_id=contract_id,
            property_id=property_id,
            agent_id=agent_id,
            status=status,
            metadata=metadata
        )
    )


async def publish_phone_call_completed(
    call_id: str,
    property_id: Optional[int],
    contact_id: Optional[int],
    agent_id: int,
    phone_number: str,
    duration_seconds: int,
    **metadata
):
    """Publish phone call completed event."""
    await event_bus.publish(
        EventType.PHONE_CALL_COMPLETED,
        PhoneCallEvent(
            call_id=call_id,
            property_id=property_id,
            contact_id=contact_id,
            agent_id=agent_id,
            phone_number=phone_number,
            status="completed",
            duration_seconds=duration_seconds,
            metadata=metadata
        )
    )
