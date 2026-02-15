"""Market Watchlist service — CRUD, matching, and notifications."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.market_watchlist import MarketWatchlist
from app.models.notification import Notification, NotificationType, NotificationPriority
from app.models.property import Property

logger = logging.getLogger(__name__)


class WatchlistService:
    """Manage saved-search watchlists and match incoming properties."""

    # ── CRUD ─────────────────────────────────────────────────────────

    def create(
        self,
        db: Session,
        agent_id: int,
        name: str,
        criteria: dict,
        description: str | None = None,
    ) -> MarketWatchlist:
        wl = MarketWatchlist(
            agent_id=agent_id,
            name=name,
            criteria=criteria,
            description=description,
        )
        db.add(wl)
        db.commit()
        db.refresh(wl)
        return wl

    def list(
        self,
        db: Session,
        agent_id: int | None = None,
        is_active: bool | None = None,
    ) -> list[MarketWatchlist]:
        q = db.query(MarketWatchlist)
        if agent_id is not None:
            q = q.filter(MarketWatchlist.agent_id == agent_id)
        if is_active is not None:
            q = q.filter(MarketWatchlist.is_active == is_active)
        return q.order_by(MarketWatchlist.created_at.desc()).all()

    def get(self, db: Session, watchlist_id: int) -> MarketWatchlist | None:
        return db.query(MarketWatchlist).filter(MarketWatchlist.id == watchlist_id).first()

    def update(self, db: Session, watchlist_id: int, **kwargs: Any) -> MarketWatchlist | None:
        wl = self.get(db, watchlist_id)
        if not wl:
            return None
        for key, value in kwargs.items():
            if hasattr(wl, key):
                setattr(wl, key, value)
        wl.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(wl)
        return wl

    def delete(self, db: Session, watchlist_id: int) -> bool:
        wl = self.get(db, watchlist_id)
        if not wl:
            return False
        db.delete(wl)
        db.commit()
        return True

    def toggle(self, db: Session, watchlist_id: int) -> MarketWatchlist | None:
        wl = self.get(db, watchlist_id)
        if not wl:
            return None
        wl.is_active = not wl.is_active
        wl.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(wl)
        return wl

    # ── Matching ─────────────────────────────────────────────────────

    def check_and_notify(self, db: Session, prop: Property) -> list[int]:
        """Check all active watchlists against a new property.

        Returns list of matched watchlist IDs.
        """
        active = db.query(MarketWatchlist).filter(MarketWatchlist.is_active.is_(True)).all()
        matched_ids: list[int] = []

        for wl in active:
            if self._property_matches(prop, wl.criteria):
                matched_ids.append(wl.id)
                wl.match_count = (wl.match_count or 0) + 1
                wl.last_matched_at = datetime.now(timezone.utc)

                # Create notification
                self._create_match_notification(db, wl, prop)

        if matched_ids:
            db.commit()

        return matched_ids

    def _property_matches(self, prop: Property, criteria: dict) -> bool:
        """AND-logic: every provided criterion must match."""
        if not criteria:
            return False

        # City — case-insensitive contains
        if "city" in criteria and criteria["city"]:
            if not prop.city or criteria["city"].lower() not in prop.city.lower():
                return False

        # State — case-insensitive exact
        if "state" in criteria and criteria["state"]:
            if not prop.state or prop.state.lower() != criteria["state"].lower():
                return False

        # Property type — exact match
        if "property_type" in criteria and criteria["property_type"]:
            prop_type = prop.property_type.value if prop.property_type else None
            if prop_type != criteria["property_type"]:
                return False

        # Price range
        if "min_price" in criteria and criteria["min_price"] is not None:
            if prop.price is None or prop.price < criteria["min_price"]:
                return False

        if "max_price" in criteria and criteria["max_price"] is not None:
            if prop.price is None or prop.price > criteria["max_price"]:
                return False

        # Bedrooms
        if "min_bedrooms" in criteria and criteria["min_bedrooms"] is not None:
            if prop.bedrooms is None or prop.bedrooms < criteria["min_bedrooms"]:
                return False

        # Bathrooms
        if "min_bathrooms" in criteria and criteria["min_bathrooms"] is not None:
            if prop.bathrooms is None or prop.bathrooms < criteria["min_bathrooms"]:
                return False

        # Square feet
        if "min_sqft" in criteria and criteria["min_sqft"] is not None:
            if prop.square_feet is None or prop.square_feet < criteria["min_sqft"]:
                return False

        return True

    def _create_match_notification(
        self, db: Session, wl: MarketWatchlist, prop: Property
    ) -> None:
        price_str = f"${prop.price:,.0f}" if prop.price else "N/A"
        address = prop.address or "Unknown address"
        city = prop.city or ""

        notif = Notification(
            type=NotificationType.GENERAL,
            priority=NotificationPriority.HIGH,
            title=f"Watchlist Match: {wl.name}",
            message=(
                f"New property matches your watchlist \"{wl.name}\": "
                f"{address}, {city} — {price_str}"
            ),
            property_id=prop.id,
            agent_id=wl.agent_id,
            icon="🎯",
            data=json.dumps({
                "watchlist_id": wl.id,
                "watchlist_name": wl.name,
                "match_type": "new_property",
            }),
        )
        db.add(notif)

    # ── Manual check ─────────────────────────────────────────────────

    def check_property(self, db: Session, property_id: int) -> dict:
        """Manually check a property against all active watchlists."""
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            return {"error": "Property not found"}

        active = db.query(MarketWatchlist).filter(MarketWatchlist.is_active.is_(True)).all()
        matches = []
        for wl in active:
            if self._property_matches(prop, wl.criteria):
                matches.append({"id": wl.id, "name": wl.name, "agent_id": wl.agent_id})

        return {
            "property_id": property_id,
            "address": prop.address,
            "total_watchlists_checked": len(active),
            "matches": matches,
            "match_count": len(matches),
        }


watchlist_service = WatchlistService()
