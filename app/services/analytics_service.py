"""Analytics service — cross-property portfolio intelligence and advanced dashboard."""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

from sqlalchemy import func, case, and_
from sqlalchemy.orm import Session

from app.models.contract import Contract, ContractStatus
from app.models.conversation_history import ConversationHistory
from app.models.property import Property, PropertyStatus, PropertyType
from app.models.skip_trace import SkipTrace
from app.models.zillow_enrichment import ZillowEnrichment
from app.models.analytics_event import AnalyticsEvent
from app.models.contact import Contact


class AnalyticsService:
    """Portfolio-level analytics aggregated from existing data."""

    def get_portfolio_summary(self, db: Session) -> dict:
        pipeline = self._pipeline_stats(db)
        value = self._portfolio_value(db)
        contracts = self._contract_stats(db)
        activity = self._activity_stats(db)
        scores = self._deal_score_stats(db)
        coverage = self._enrichment_coverage(db)

        voice_summary = self._build_voice_summary(pipeline, value, contracts, scores)

        return {
            "pipeline": pipeline,
            "portfolio_value": value,
            "contracts": contracts,
            "activity": activity,
            "deal_scores": scores,
            "enrichment_coverage": coverage,
            "voice_summary": voice_summary,
        }

    def get_pipeline_summary(self, db: Session) -> dict:
        pipeline = self._pipeline_stats(db)
        total = pipeline.get("total", 0)
        parts = [f"{total} total properties."]
        for status, count in pipeline.get("by_status", {}).items():
            if count > 0:
                parts.append(f"{count} {status}.")
        return {
            "pipeline": pipeline,
            "voice_summary": " ".join(parts),
        }

    def get_contract_summary(self, db: Session) -> dict:
        contracts = self._contract_stats(db)
        total = contracts.get("total", 0)
        unsigned = contracts.get("unsigned_required", 0)
        parts = [f"{total} total contracts."]
        if unsigned:
            parts.append(f"{unsigned} required contracts still need signatures.")
        for status, count in contracts.get("by_status", {}).items():
            if count > 0:
                parts.append(f"{count} {status}.")
        return {
            "contracts": contracts,
            "voice_summary": " ".join(parts),
        }

    # ── Stats helpers ──

    def _pipeline_stats(self, db: Session) -> dict:
        total = db.query(func.count(Property.id)).scalar() or 0

        by_status = {}
        for status in PropertyStatus:
            count = db.query(func.count(Property.id)).filter(Property.status == status).scalar() or 0
            if count > 0:
                by_status[status.value] = count

        by_type = {}
        for ptype in PropertyType:
            count = db.query(func.count(Property.id)).filter(Property.property_type == ptype).scalar() or 0
            if count > 0:
                by_type[ptype.value] = count

        return {"total": total, "by_status": by_status, "by_type": by_type}

    def _portfolio_value(self, db: Session) -> dict:
        total_price = db.query(func.sum(Property.price)).scalar() or 0
        avg_price = db.query(func.avg(Property.price)).scalar() or 0
        total_zestimate = (
            db.query(func.sum(ZillowEnrichment.zestimate))
            .join(Property)
            .scalar()
        ) or 0

        return {
            "total_price": round(total_price, 2),
            "avg_price": round(avg_price, 2),
            "total_zestimate": round(total_zestimate, 2),
            "equity": round(total_zestimate - total_price, 2),
        }

    def _contract_stats(self, db: Session) -> dict:
        total = db.query(func.count(Contract.id)).scalar() or 0

        by_status = {}
        for status in ContractStatus:
            count = db.query(func.count(Contract.id)).filter(Contract.status == status).scalar() or 0
            if count > 0:
                by_status[status.value] = count

        unsigned_required = (
            db.query(func.count(Contract.id))
            .filter(
                Contract.is_required.is_(True),
                Contract.status.in_([ContractStatus.DRAFT, ContractStatus.SENT, ContractStatus.PENDING_SIGNATURE]),
            )
            .scalar()
        ) or 0

        return {
            "total": total,
            "by_status": by_status,
            "unsigned_required": unsigned_required,
        }

    def _activity_stats(self, db: Session) -> dict:
        now = datetime.now(timezone.utc)

        def count_since(hours):
            cutoff = now - timedelta(hours=hours)
            return db.query(func.count(ConversationHistory.id)).filter(
                ConversationHistory.created_at >= cutoff
            ).scalar() or 0

        # Most active properties (last 7 days)
        week_ago = now - timedelta(days=7)
        most_active = (
            db.query(
                ConversationHistory.property_id,
                func.count(ConversationHistory.id).label("action_count"),
            )
            .filter(
                ConversationHistory.property_id.isnot(None),
                ConversationHistory.created_at >= week_ago,
            )
            .group_by(ConversationHistory.property_id)
            .order_by(func.count(ConversationHistory.id).desc())
            .limit(5)
            .all()
        )

        most_active_list = []
        for row in most_active:
            prop = db.query(Property).filter(Property.id == row.property_id).first()
            most_active_list.append({
                "property_id": row.property_id,
                "address": prop.address if prop else "Unknown",
                "action_count": row.action_count,
            })

        return {
            "last_24h": count_since(24),
            "last_7d": count_since(168),
            "last_30d": count_since(720),
            "most_active_properties": most_active_list,
        }

    def _deal_score_stats(self, db: Session) -> dict:
        scored = db.query(Property).filter(Property.deal_score.isnot(None)).all()
        if not scored:
            return {"avg_score": None, "distribution": {}, "top_5": []}

        avg = sum(p.deal_score for p in scored) / len(scored)

        distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        for p in scored:
            grade = p.score_grade or "F"
            if grade in distribution:
                distribution[grade] += 1

        top_5 = sorted(scored, key=lambda p: p.deal_score or 0, reverse=True)[:5]
        top_5_list = [
            {
                "property_id": p.id,
                "address": p.address,
                "deal_score": p.deal_score,
                "grade": p.score_grade,
            }
            for p in top_5
        ]

        return {
            "avg_score": round(avg, 1),
            "distribution": distribution,
            "top_5": top_5_list,
        }

    def _enrichment_coverage(self, db: Session) -> dict:
        total = db.query(func.count(Property.id)).scalar() or 0
        if total == 0:
            return {"total": 0, "zillow_pct": 0, "skip_trace_pct": 0}

        with_zillow = (
            db.query(func.count(ZillowEnrichment.id))
            .join(Property)
            .scalar()
        ) or 0

        with_skip = (
            db.query(func.count(func.distinct(SkipTrace.property_id)))
            .scalar()
        ) or 0

        return {
            "total": total,
            "with_zillow": with_zillow,
            "zillow_pct": round(with_zillow / total * 100, 1),
            "with_skip_trace": with_skip,
            "skip_trace_pct": round(with_skip / total * 100, 1),
        }

    # ── Voice summary ──

    def _build_voice_summary(self, pipeline, value, contracts, scores) -> str:
        total = pipeline.get("total", 0)
        if total == 0:
            return "Your portfolio is empty. Add some properties to get started."

        parts = [f"You have {total} properties worth ${value['total_price']:,.0f} total."]

        waiting = pipeline.get("by_status", {}).get("waiting_for_contracts", 0)
        if waiting:
            parts.append(f"{waiting} waiting for contracts.")

        unsigned = contracts.get("unsigned_required", 0)
        if unsigned:
            parts.append(f"{unsigned} contracts need signatures.")

        if scores.get("top_5"):
            top = scores["top_5"][0]
            parts.append(
                f"Best deal: property #{top['property_id']} at {top['address']} "
                f"(score {top['deal_score']:.0f}, grade {top['grade']})."
            )

        return " ".join(parts)

    # ============================================================
    # Advanced Dashboard Features
    # ============================================================

    def get_dashboard_overview(self, db: Session, agent_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Get key performance indicators for the dashboard.
        """
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Event counts
        property_views = db.query(func.count(AnalyticsEvent.id)).filter(
            and_(
                AnalyticsEvent.agent_id == agent_id,
                AnalyticsEvent.event_type == "property_view",
                AnalyticsEvent.created_at >= start_date
            )
        ).scalar() or 0

        leads_created = db.query(func.count(AnalyticsEvent.id)).filter(
            and_(
                AnalyticsEvent.agent_id == agent_id,
                AnalyticsEvent.event_type == "lead_created",
                AnalyticsEvent.created_at >= start_date
            )
        ).scalar() or 0

        conversions = db.query(func.count(AnalyticsEvent.id)).filter(
            and_(
                AnalyticsEvent.agent_id == agent_id,
                AnalyticsEvent.event_type == "conversion",
                AnalyticsEvent.created_at >= start_date
            )
        ).scalar() or 0

        # Total value (revenue attribution)
        total_value = db.query(func.sum(AnalyticsEvent.value)).filter(
            and_(
                AnalyticsEvent.agent_id == agent_id,
                AnalyticsEvent.created_at >= start_date
            )
        ).scalar() or 0

        # Active properties
        active_properties = db.query(func.count(Property.id)).filter(
            and_(
                Property.agent_id == agent_id,
                Property.status != PropertyStatus.COMPLETE
            )
        ).scalar() or 0

        # New properties this period
        new_properties = db.query(func.count(Property.id)).filter(
            and_(
                Property.agent_id == agent_id,
                Property.created_at >= start_date
            )
        ).scalar() or 0

        # Contracts signed (join through Property)
        contracts_signed = db.query(func.count(Contract.id)).join(
            Property, Contract.property_id == Property.id
        ).filter(
            and_(
                Property.agent_id == agent_id,
                Contract.status == ContractStatus.COMPLETED,
                Contract.updated_at >= start_date
            )
        ).scalar() or 0

        return {
            "period_days": days,
            "property_views": property_views,
            "leads_created": leads_created,
            "conversions": conversions,
            "conversion_rate": round((conversions / leads_created * 100) if leads_created > 0 else 0, 2),
            "total_value_cents": total_value,
            "total_value_usd": total_value / 100 if total_value else 0,
            "active_properties": active_properties,
            "new_properties": new_properties,
            "contracts_signed": contracts_signed,
        }

    def get_events_trend(
        self, db: Session,
        agent_id: int,
        event_type: Optional[str] = None,
        days: int = 30,
        granularity: str = "day"
    ) -> List[Dict[str, Any]]:
        """Get event counts over time for line charts."""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        query = db.query(
            func.date_trunc(granularity, AnalyticsEvent.created_at).label("date"),
            func.count(AnalyticsEvent.id).label("count")
        ).filter(
            and_(
                AnalyticsEvent.agent_id == agent_id,
                AnalyticsEvent.created_at >= start_date
            )
        )

        if event_type:
            query = query.filter(AnalyticsEvent.event_type == event_type)

        results = query.group_by("date").order_by("date").all()

        return [
            {"date": result.date.isoformat() if result.date else None, "count": result.count}
            for result in results
        ]

    def get_conversion_funnel(self, db: Session, agent_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """Get conversion funnel data."""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        stages = [
            ("property_view", "Property Views"),
            ("lead_created", "Leads Captured"),
            ("contact_added", "Contacts Added"),
            ("contract_sent", "Contracts Sent"),
            ("contract_signed", "Deals Closed"),
        ]

        funnel_data = []

        for event_type, stage_name in stages:
            count = db.query(func.count(AnalyticsEvent.id)).filter(
                and_(
                    AnalyticsEvent.agent_id == agent_id,
                    AnalyticsEvent.event_type == event_type,
                    AnalyticsEvent.created_at >= start_date
                )
            ).scalar() or 0

            # For contact_added, count from contacts table (join through Property)
            if event_type == "contact_added":
                count = db.query(func.count(Contact.id)).join(
                    Property, Contact.property_id == Property.id
                ).filter(
                    and_(
                        Property.agent_id == agent_id,
                        Contact.created_at >= start_date
                    )
                ).scalar() or 0

            funnel_data.append({"stage": stage_name, "count": count})

        return funnel_data

    def get_top_properties(self, db: Session, agent_id: int, days: int = 30, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most viewed properties."""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        results = db.query(
            AnalyticsEvent.property_id,
            Property.address,
            Property.city,
            Property.state,
            func.count(AnalyticsEvent.id).label("view_count")
        ).join(
            Property, AnalyticsEvent.property_id == Property.id
        ).filter(
            and_(
                AnalyticsEvent.agent_id == agent_id,
                AnalyticsEvent.event_type == "property_view",
                AnalyticsEvent.created_at >= start_date
            )
        ).group_by(
            AnalyticsEvent.property_id,
            Property.address,
            Property.city,
            Property.state
        ).order_by(
            func.count(AnalyticsEvent.id).desc()
        ).limit(limit).all()

        return [
            {
                "property_id": result.property_id,
                "address": result.address,
                "city": result.city,
                "state": result.state,
                "view_count": result.view_count,
            }
            for result in results
        ]

    def get_traffic_sources(self, db: Session, agent_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """Get traffic breakdown by UTM source."""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        results = db.query(
            func.coalesce(AnalyticsEvent.utm_source, "direct").label("source"),
            func.count(AnalyticsEvent.id).label("count")
        ).filter(
            and_(
                AnalyticsEvent.agent_id == agent_id,
                AnalyticsEvent.created_at >= start_date
            )
        ).group_by("source").order_by(func.count(AnalyticsEvent.id).desc()).all()

        total_count = sum(result.count for result in results)

        return [
            {
                "source": result.source,
                "count": result.count,
                "percentage": round((result.count / total_count * 100) if total_count > 0 else 0, 2),
            }
            for result in results
        ]

    def get_geo_distribution(self, db: Session, agent_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """Get lead distribution by city."""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        results = db.query(
            Property.city,
            func.count(AnalyticsEvent.id).label("count")
        ).join(
            Property, AnalyticsEvent.property_id == Property.id
        ).filter(
            and_(
                AnalyticsEvent.agent_id == agent_id,
                AnalyticsEvent.event_type == "property_view",
                AnalyticsEvent.created_at >= start_date
            )
        ).group_by(Property.city).order_by(func.count(AnalyticsEvent.id).desc()).limit(20).all()

        return [
            {"city": result.city, "count": result.count}
            for result in results
        ]

    def get_chart_data(
        self, db: Session,
        agent_id: int,
        chart_type: str,
        dimension: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get data for various chart types.

        Chart types: line, pie, bar
        Dimensions: property_views, leads_created, traffic_source, city
        """
        if chart_type == "line":
            return self._get_line_chart(db, agent_id, dimension, days)
        elif chart_type == "pie":
            return self._get_pie_chart(db, agent_id, dimension, days)
        elif chart_type == "bar":
            return self._get_bar_chart(db, agent_id, dimension, days)
        else:
            return {"error": f"Unknown chart type: {chart_type}"}

    def _get_line_chart(self, db: Session, agent_id: int, metric: str, days: int) -> Dict[str, Any]:
        """Get data for line charts."""
        event_type_mapping = {
            "property_views": "property_view",
            "leads_created": "lead_created",
            "conversions": "conversion",
        }

        event_type = event_type_mapping.get(metric, "property_view")
        data = self.get_events_trend(db, agent_id, event_type, days)

        return {
            "chart_type": "line",
            "metric": metric,
            "data": data,
        }

    def _get_pie_chart(self, db: Session, agent_id: int, dimension: str, days: int) -> Dict[str, Any]:
        """Get data for pie charts."""
        if dimension == "traffic_source":
            traffic_data = self.get_traffic_sources(db, agent_id, days)
            return {
                "chart_type": "pie",
                "dimension": dimension,
                "labels": [item["source"] for item in traffic_data],
                "values": [item["count"] for item in traffic_data],
            }
        elif dimension == "property_type":
            # Get property type distribution
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            results = db.query(
                Property.property_type,
                func.count(AnalyticsEvent.id).label("count")
            ).join(
                Property, AnalyticsEvent.property_id == Property.id
            ).filter(
                and_(
                    AnalyticsEvent.agent_id == agent_id,
                    AnalyticsEvent.event_type == "property_view",
                    AnalyticsEvent.created_at >= start_date
                )
            ).group_by(Property.property_type).all()

            return {
                "chart_type": "pie",
                "dimension": dimension,
                "labels": [result.property_type or "Unknown" for result in results],
                "values": [result.count for result in results],
            }
        elif dimension == "city":
            geo_data = self.get_geo_distribution(db, agent_id, days)
            return {
                "chart_type": "pie",
                "dimension": dimension,
                "labels": [item["city"] for item in geo_data[:10]],
                "values": [item["count"] for item in geo_data[:10]],
            }
        else:
            return {"error": f"Unknown dimension: {dimension}"}

    def _get_bar_chart(self, db: Session, agent_id: int, dimension: str, days: int) -> Dict[str, Any]:
        """Get data for bar charts."""
        if dimension == "top_properties":
            top_properties = self.get_top_properties(db, agent_id, days)

            return {
                "chart_type": "bar",
                "dimension": dimension,
                "x": [f"{p['city']}, {p['state']}" for p in top_properties],
                "y": [p["view_count"] for p in top_properties],
                "labels": [p["address"] for p in top_properties],
            }
        else:
            return {"error": f"Unknown dimension: {dimension}"}

    @staticmethod
    def track_event(
        db: Session,
        agent_id: int,
        event_type: str,
        event_name: str,
        properties: Dict[str, Any],
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        property_id: Optional[int] = None,
        value: Optional[int] = None,
        referrer: Optional[str] = None,
        utm_source: Optional[str] = None,
        utm_medium: Optional[str] = None,
        utm_campaign: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AnalyticsEvent:
        """Track an analytics event."""
        event = AnalyticsEvent(
            agent_id=agent_id,
            event_type=event_type,
            event_name=event_name,
            properties=properties,
            session_id=session_id,
            user_id=user_id,
            property_id=property_id,
            value=value,
            referrer=referrer,
            utm_source=utm_source,
            utm_medium=utm_medium,
            utm_campaign=utm_campaign,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        db.add(event)
        db.commit()
        db.refresh(event)

        return event


analytics_service = AnalyticsService()
