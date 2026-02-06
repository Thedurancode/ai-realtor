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

    def remember_objection(self, db: Session, session_id: str, text: str, topic: str | None = None) -> VoiceMemoryNode:
        key = sha1(f"{text}|{topic or ''}".encode("utf-8")).hexdigest()[:16]
        payload = {"text": text, "topic": topic, "kind": "objection"}
        return self.upsert_node(
            db,
            session_id=session_id,
            node_type="objection",
            node_key=key,
            summary=text[:200],
            payload=payload,
            importance=0.8,
        )

    def remember_promise(
        self,
        db: Session,
        session_id: str,
        promise_text: str,
        due_at: str | None = None,
        fulfilled: bool = False,
    ) -> VoiceMemoryNode:
        key = sha1(f"{promise_text}|{due_at or ''}".encode("utf-8")).hexdigest()[:16]
        payload = {
            "text": promise_text,
            "due_at": due_at,
            "fulfilled": fulfilled,
            "kind": "promise",
        }
        return self.upsert_node(
            db,
            session_id=session_id,
            node_type="promise",
            node_key=key,
            summary=promise_text[:200],
            payload=payload,
            importance=0.85,
        )

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
