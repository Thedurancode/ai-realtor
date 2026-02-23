"""Persistent memory graph for voice sessions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha1
from typing import Any

from sqlalchemy.orm import Session

from app.models.voice_memory import VoiceMemoryEdge, VoiceMemoryNode


@dataclass
class MemoryRef:
    node_type: str
    node_key: str


class MemoryGraphService:
    """Store and retrieve durable conversational context as a graph."""

    def upsert_node(
        self,
        db: Session,
        session_id: str,
        node_type: str,
        node_key: str,
        summary: str | None = None,
        payload: dict[str, Any] | None = None,
        importance: float = 0.5,
    ) -> VoiceMemoryNode:
        node = (
            db.query(VoiceMemoryNode)
            .filter(
                VoiceMemoryNode.session_id == session_id,
                VoiceMemoryNode.node_type == node_type,
                VoiceMemoryNode.node_key == node_key,
            )
            .first()
        )

        now = datetime.utcnow()
        if node is None:
            node = VoiceMemoryNode(
                session_id=session_id,
                node_type=node_type,
                node_key=node_key,
                summary=summary,
                payload=payload,
                importance=importance,
                last_seen_at=now,
            )
            db.add(node)
            db.flush()
            return node

        node.summary = summary or node.summary
        node.payload = payload if payload is not None else node.payload
        node.importance = max(node.importance, importance)
        node.last_seen_at = now
        db.flush()
        return node

    def upsert_edge(
        self,
        db: Session,
        session_id: str,
        source: MemoryRef,
        target: MemoryRef,
        relation: str,
        weight: float = 1.0,
        payload: dict[str, Any] | None = None,
    ) -> VoiceMemoryEdge:
        source_node = self.upsert_node(
            db,
            session_id=session_id,
            node_type=source.node_type,
            node_key=source.node_key,
        )
        target_node = self.upsert_node(
            db,
            session_id=session_id,
            node_type=target.node_type,
            node_key=target.node_key,
        )

        edge = (
            db.query(VoiceMemoryEdge)
            .filter(
                VoiceMemoryEdge.session_id == session_id,
                VoiceMemoryEdge.source_node_id == source_node.id,
                VoiceMemoryEdge.target_node_id == target_node.id,
                VoiceMemoryEdge.relation == relation,
            )
            .first()
        )

        now = datetime.utcnow()
        if edge is None:
            edge = VoiceMemoryEdge(
                session_id=session_id,
                source_node_id=source_node.id,
                target_node_id=target_node.id,
                relation=relation,
                weight=weight,
                payload=payload,
                last_seen_at=now,
            )
            db.add(edge)
            db.flush()
            return edge

        edge.weight = max(edge.weight, weight)
        edge.payload = payload if payload is not None else edge.payload
        edge.last_seen_at = now
        db.flush()
        return edge

    def remember_session_state(self, db: Session, session_id: str, key: str, value: Any) -> VoiceMemoryNode:
        value_payload = {"value": value}
        return self.upsert_node(
            db,
            session_id=session_id,
            node_type="session_state",
            node_key=key,
            summary=str(value),
            payload=value_payload,
            importance=0.9,
        )

    def get_session_state(self, db: Session, session_id: str, key: str) -> Any | None:
        node = (
            db.query(VoiceMemoryNode)
            .filter(
                VoiceMemoryNode.session_id == session_id,
                VoiceMemoryNode.node_type == "session_state",
                VoiceMemoryNode.node_key == key,
            )
            .first()
        )
        if not node or not node.payload:
            return None
        return node.payload.get("value")

    def remember_property(
        self,
        db: Session,
        session_id: str,
        property_id: int,
        address: str | None = None,
        city: str | None = None,
        state: str | None = None,
    ) -> VoiceMemoryNode:
        payload = {
            "property_id": property_id,
            "address": address,
            "city": city,
            "state": state,
        }
        node = self.upsert_node(
            db,
            session_id=session_id,
            node_type="property",
            node_key=str(property_id),
            summary=address,
            payload=payload,
            importance=0.95,
        )
        self.remember_session_state(db, session_id, "last_property_id", property_id)
        if address:
            self.remember_session_state(db, session_id, "last_property_address", address)
        return node

    def remember_contact(
        self,
        db: Session,
        session_id: str,
        contact_id: int,
        name: str,
        role: str | None = None,
        property_id: int | None = None,
    ) -> VoiceMemoryNode:
        payload = {
            "contact_id": contact_id,
            "name": name,
            "role": role,
            "property_id": property_id,
        }
        node = self.upsert_node(
            db,
            session_id=session_id,
            node_type="contact",
            node_key=str(contact_id),
            summary=name,
            payload=payload,
            importance=0.9,
        )
        self.remember_session_state(db, session_id, "last_contact_id", contact_id)
        self.remember_session_state(db, session_id, "last_contact_name", name)

        if property_id is not None:
            self.upsert_edge(
                db,
                session_id=session_id,
                source=MemoryRef("contact", str(contact_id)),
                target=MemoryRef("property", str(property_id)),
                relation="associated_with",
                weight=0.9,
            )
        return node

    def remember_contract(
        self,
        db: Session,
        session_id: str,
        contract_id: int,
        name: str,
        status: str | None = None,
        property_id: int | None = None,
        contact_id: int | None = None,
    ) -> VoiceMemoryNode:
        payload = {
            "contract_id": contract_id,
            "name": name,
            "status": status,
            "property_id": property_id,
            "contact_id": contact_id,
        }
        node = self.upsert_node(
            db,
            session_id=session_id,
            node_type="contract",
            node_key=str(contract_id),
            summary=name,
            payload=payload,
            importance=0.9,
        )
        self.remember_session_state(db, session_id, "last_contract_id", contract_id)
        self.remember_session_state(db, session_id, "last_contract_name", name)

        if property_id is not None:
            self.upsert_edge(
                db,
                session_id=session_id,
                source=MemoryRef("contract", str(contract_id)),
                target=MemoryRef("property", str(property_id)),
                relation="for_property",
                weight=0.95,
            )
        if contact_id is not None:
            self.upsert_edge(
                db,
                session_id=session_id,
                source=MemoryRef("contract", str(contract_id)),
                target=MemoryRef("contact", str(contact_id)),
                relation="for_contact",
                weight=0.85,
            )
        return node

    # ─── SPACEBOT-ALIGNED MEMORY TYPES ───

    def remember_fact(self, db: Session, session_id: str, fact: str, category: str | None = None) -> VoiceMemoryNode:
        """Store a learned fact (Spacebot: 'Fact' type).
        Examples: 'Property 5 has a pool', 'Miami market is up 5%', 'Closing takes 30 days'
        """
        key = sha1(f"{fact}|{category or ''}".encode("utf-8")).hexdigest()[:16]
        payload = {"fact": fact, "category": category, "kind": "fact"}
        return self.upsert_node(
            db,
            session_id=session_id,
            node_type="fact",
            node_key=key,
            summary=fact[:200],
            payload=payload,
            importance=0.75,
        )

    def remember_preference(self, db: Session, session_id: str, preference: str, entity_type: str | None = None, entity_id: str | None = None) -> VoiceMemoryNode:
        """Store user preferences (Spacebot: 'Preference' type).
        Examples: 'Prefers condos over houses', 'Wants properties under $500k', 'Likes modern kitchens'
        """
        key = sha1(f"{preference}|{entity_type or ''}|{entity_id or ''}".encode("utf-8")).hexdigest()[:16]
        payload = {"preference": preference, "entity_type": entity_type, "entity_id": entity_id, "kind": "preference"}
        node = self.upsert_node(
            db,
            session_id=session_id,
            node_type="preference",
            node_key=key,
            summary=preference[:200],
            payload=payload,
            importance=0.85,
        )

        # Link to entity if provided
        if entity_type and entity_id:
            self.upsert_edge(
                db,
                session_id=session_id,
                source=MemoryRef("preference", key),
                target=MemoryRef(entity_type, str(entity_id)),
                relation="preference_for",
                weight=0.9,
            )
        return node

    def remember_decision(self, db: Session, session_id: str, decision: str, context: dict[str, Any] | None = None) -> VoiceMemoryNode:
        """Store decisions made (Spacebot: 'Decision' type).
        Examples: 'Selected offer at $480k', 'Chose FHA financing', 'Decided to counter-offer'
        """
        key = sha1(f"{decision}|{datetime.utcnow().isoformat()}".encode("utf-8")).hexdigest()[:16]
        payload = {"decision": decision, "context": context or {}, "timestamp": datetime.utcnow().isoformat(), "kind": "decision"}
        return self.upsert_node(
            db,
            session_id=session_id,
            node_type="decision",
            node_key=key,
            summary=decision[:200],
            payload=payload,
            importance=0.95,
        )

    def remember_identity(self, db: Session, session_id: str, entity_type: str, entity_id: str, identity_data: dict[str, Any]) -> VoiceMemoryNode:
        """Store identity information (Spacebot: 'Identity' type).
        Examples: 'John Smith is a first-time buyer', 'Property 5 is a luxury condo', 'Seller is motivated'
        """
        key = f"{entity_type}_{entity_id}"
        payload = {"entity_type": entity_type, "entity_id": entity_id, **identity_data, "kind": "identity"}
        summary = identity_data.get("summary", f"{entity_type} {entity_id}")

        # First, ensure the entity node exists
        if entity_type == "contact":
            self.upsert_node(
                db, session_id, node_type="contact", node_key=str(entity_id),
                summary=identity_data.get("name"), payload=identity_data, importance=0.9
            )
        elif entity_type == "property":
            self.upsert_node(
                db, session_id, node_type="property", node_key=str(entity_id),
                summary=identity_data.get("address"), payload=identity_data, importance=0.95
            )

        # Now create the identity node
        node = self.upsert_node(
            db,
            session_id=session_id,
            node_type="identity",
            node_key=key,
            summary=summary,
            payload=payload,
            importance=0.92,
        )

        # Link identity to entity
        self.upsert_edge(
            db,
            session_id=session_id,
            source=MemoryRef("identity", key),
            target=MemoryRef(entity_type, str(entity_id)),
            relation="describes",
            weight=0.95,
        )
        return node

    def remember_event(self, db: Session, session_id: str, event_type: str, description: str, entities: list[dict[str, str]] | None = None, timestamp: datetime | None = None) -> VoiceMemoryNode:
        """Store events that happened (Spacebot: 'Event' type).
        Examples: 'Phone call with John Smith', 'Property showing at 123 Main St', 'Contract signed'
        """
        key = sha1(f"{event_type}|{description}|{(timestamp or datetime.utcnow()).isoformat()}".encode("utf-8")).hexdigest()[:16]
        payload = {
            "event_type": event_type,
            "description": description,
            "entities": entities or [],
            "timestamp": (timestamp or datetime.utcnow()).isoformat(),
            "kind": "event"
        }
        node = self.upsert_node(
            db,
            session_id=session_id,
            node_type="event",
            node_key=key,
            summary=description[:200],
            payload=payload,
            importance=0.88,
        )

        # Link event to involved entities
        if entities:
            for entity in entities:
                entity_type = entity.get("type")
                entity_id = entity.get("id")
                if entity_type and entity_id:
                    self.upsert_edge(
                        db,
                        session_id=session_id,
                        source=MemoryRef("event", key),
                        target=MemoryRef(entity_type, str(entity_id)),
                        relation="involved",
                        weight=0.85,
                    )
        return node

    def remember_observation(self, db: Session, session_id: str, observation: str, category: str | None = None, confidence: float = 0.8) -> VoiceMemoryNode:
        """Store agent observations (Spacebot: 'Observation' type).
        Examples: 'Market is slowing down', 'Buyers are negotiating harder', 'Properties under $400k move fast'
        """
        key = sha1(f"{observation}|{category or ''}".encode("utf-8")).hexdigest()[:16]
        payload = {"observation": observation, "category": category, "confidence": confidence, "kind": "observation"}
        return self.upsert_node(
            db,
            session_id=session_id,
            node_type="observation",
            node_key=key,
            summary=observation[:200],
            payload=payload,
            importance=0.82,
        )

    def remember_goal(self, db: Session, session_id: str, goal: str, metadata: dict[str, Any] | None = None, priority: str = "high") -> VoiceMemoryNode:
        """Store goals to achieve (Spacebot: 'Goal' type).
        Examples: 'Close deal on property 5 by Friday', 'Find 3 Miami condos under $400k'
        """
        key = sha1(f"{goal}|{datetime.utcnow().isoformat()}".encode("utf-8")).hexdigest()[:16]
        payload = {"goal": goal, "metadata": metadata or {}, "priority": priority, "kind": "goal"}

        # Adjust importance based on priority
        importance_map = {"critical": 1.0, "high": 0.95, "medium": 0.85, "low": 0.75}
        importance = importance_map.get(priority.lower(), 0.9)

        return self.upsert_node(
            db,
            session_id=session_id,
            node_type="goal",
            node_key=key,
            summary=goal[:250],
            payload=payload,
            importance=importance,
        )

    def remember_todo(self, db: Session, session_id: str, task: str, due_at: str | None = None, property_id: int | None = None, contact_id: int | None = None) -> VoiceMemoryNode:
        """Store actionable todos (Spacebot: 'Todo' type).
        Examples: 'Call John Smith by Friday', 'Send contract by 5 PM', 'Follow up on property 5'
        """
        key = sha1(f"{task}|{due_at or ''}".encode("utf-8")).hexdigest()[:16]
        payload = {
            "task": task,
            "due_at": due_at,
            "property_id": property_id,
            "contact_id": contact_id,
            "completed": False,
            "kind": "todo"
        }
        node = self.upsert_node(
            db,
            session_id=session_id,
            node_type="todo",
            node_key=key,
            summary=task[:200],
            payload=payload,
            importance=0.90,
        )

        # Link to property/contact if specified
        if property_id is not None:
            self.upsert_edge(
                db, session_id, source=MemoryRef("todo", key),
                target=MemoryRef("property", str(property_id)), relation="for_property", weight=0.9
            )
        if contact_id is not None:
            self.upsert_edge(
                db, session_id, source=MemoryRef("todo", key),
                target=MemoryRef("contact", str(contact_id)), relation="for_contact", weight=0.9
            )
        return node

    # ─── LEGACY SUPPORT (mapped to new types) ───

    def remember_objection(self, db: Session, session_id: str, text: str, topic: str | None = None) -> VoiceMemoryNode:
        """Legacy method - now mapped to 'preference' type."""
        return self.remember_preference(db, session_id, preference=text, entity_type="objection", entity_id=topic)

    def remember_promise(
        self,
        db: Session,
        session_id: str,
        promise_text: str,
        due_at: str | None = None,
        fulfilled: bool = False,
    ) -> VoiceMemoryNode:
        """Legacy method - now mapped to 'todo' type."""
        node = self.remember_todo(
            db,
            session_id=session_id,
            task=promise_text,
            due_at=due_at,
        )
        # Update payload to include promise-specific fields
        if node.payload:
            node.payload["fulfilled"] = fulfilled
            node.payload["kind"] = "promise"
        return node

    def remember_goal(self, db: Session, session_id: str, goal: str, metadata: dict[str, Any] | None = None) -> VoiceMemoryNode:
        key = sha1(f"{goal}|{datetime.utcnow().isoformat()}".encode("utf-8")).hexdigest()[:16]
        payload = {"goal": goal, "metadata": metadata or {}}
        return self.upsert_node(
            db,
            session_id=session_id,
            node_type="goal",
            node_key=key,
            summary=goal[:250],
            payload=payload,
            importance=1.0,
        )

    def get_session_summary(self, db: Session, session_id: str, max_nodes: int = 25) -> dict[str, Any]:
        nodes = (
            db.query(VoiceMemoryNode)
            .filter(VoiceMemoryNode.session_id == session_id)
            .order_by(VoiceMemoryNode.last_seen_at.desc())
            .limit(max_nodes)
            .all()
        )
        edges = (
            db.query(VoiceMemoryEdge)
            .filter(VoiceMemoryEdge.session_id == session_id)
            .order_by(VoiceMemoryEdge.last_seen_at.desc())
            .limit(max_nodes)
            .all()
        )

        def _state(key: str) -> Any | None:
            return self.get_session_state(db, session_id, key)

        recent_nodes = [
            {
                "id": n.id,
                "node_type": n.node_type,
                "node_key": n.node_key,
                "summary": n.summary,
                "payload": n.payload,
                "importance": n.importance,
                "last_seen_at": n.last_seen_at.isoformat() if n.last_seen_at else None,
            }
            for n in nodes
        ]

        recent_edges = [
            {
                "id": e.id,
                "source_node_id": e.source_node_id,
                "target_node_id": e.target_node_id,
                "relation": e.relation,
                "weight": e.weight,
                "payload": e.payload,
                "last_seen_at": e.last_seen_at.isoformat() if e.last_seen_at else None,
            }
            for e in edges
        ]

        return {
            "session_id": session_id,
            "session_state": {
                "last_property_id": _state("last_property_id"),
                "last_property_address": _state("last_property_address"),
                "last_contact_id": _state("last_contact_id"),
                "last_contact_name": _state("last_contact_name"),
                "last_contract_id": _state("last_contract_id"),
                "last_contract_name": _state("last_contract_name"),
            },
            "recent_nodes": recent_nodes,
            "recent_edges": recent_edges,
            "node_count": len(recent_nodes),
            "edge_count": len(recent_edges),
        }

    def clear_session(self, db: Session, session_id: str) -> dict[str, int]:
        """Delete all graph memory for a session."""
        edges_deleted = (
            db.query(VoiceMemoryEdge)
            .filter(VoiceMemoryEdge.session_id == session_id)
            .delete(synchronize_session=False)
        )
        nodes_deleted = (
            db.query(VoiceMemoryNode)
            .filter(VoiceMemoryNode.session_id == session_id)
            .delete(synchronize_session=False)
        )
        db.flush()
        return {"nodes_deleted": nodes_deleted, "edges_deleted": edges_deleted}


memory_graph_service = MemoryGraphService()
