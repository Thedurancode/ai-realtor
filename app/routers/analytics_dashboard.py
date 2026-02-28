"""
Advanced Analytics Dashboard API

Provides endpoints for:
- Overview stats (KPI cards)
- Time series data (line charts)
- Conversion funnel
- Top properties
- Traffic sources
- Geographic distribution
- Chart data generation
- PDF export
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from app.database import get_db
from app.services.analytics_service import AnalyticsService
from app.auth import get_current_agent
from app.models.analytics_event import AnalyticsEvent
from app.models.dashboard import Dashboard

router = APIRouter(prefix="/analytics/dashboard", tags=["analytics_dashboard"])


# ============================================================
# Pydantic Models
# ============================================================

class EventTrackingSchema(BaseModel):
    """Schema for tracking analytics events."""

    event_type: str = Field(..., description="Event type (e.g., property_view, lead_created)")
    event_name: str = Field(..., description="Event name")
    properties: dict = Field(default_factory=dict, description="Event properties")
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    property_id: Optional[int] = None
    value: Optional[int] = Field(None, description="Value in cents (for revenue tracking)")
    referrer: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None


class DashboardCreateSchema(BaseModel):
    """Schema for creating a dashboard."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_public: bool = False
    layout: dict = Field(..., description="Widget layout configuration")
    widgets: dict = Field(..., description="Widget configurations")
    filters: Optional[dict] = None
    auto_refresh: bool = False
    refresh_interval_seconds: int = Field(300, ge=30, le=3600)
    theme: str = Field("default", pattern="^(default|dark|light)$")


class DashboardUpdateSchema(BaseModel):
    """Schema for updating a dashboard."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_public: Optional[bool] = None
    layout: Optional[dict] = None
    widgets: Optional[dict] = None
    filters: Optional[dict] = None
    auto_refresh: Optional[bool] = None
    refresh_interval_seconds: Optional[int] = Field(None, ge=30, le=3600)
    theme: Optional[str] = Field(None, pattern="^(default|dark|light)$")


# ============================================================
# Analytics Endpoints
# ============================================================

@router.get("/overview")
def get_overview_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: Session = Depends(get_db),
    current_agent = Depends(get_current_agent),
):
    """
    Get overview statistics for the dashboard.

    Returns KPI cards with:
    - Property views
    - Leads created
    - Conversions
    - Total value
    - Active properties
    - New properties
    - Contracts signed
    """
    service = AnalyticsService(db)
    stats = service.get_dashboard_overview(current_agent.id, days)
    return stats


@router.get("/trend")
def get_events_trend(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    days: int = Query(30, ge=1, le=365),
    granularity: str = Query("day", pattern="^(day|week|month)$"),
    db: Session = Depends(get_db),
    current_agent = Depends(get_current_agent),
):
    """
    Get event counts over time for line charts.

    Event types: property_view, lead_created, conversion, page_view
    """
    service = AnalyticsService(db)
    data = service.get_events_trend(current_agent.id, event_type, days, granularity)
    return {"data": data}


@router.get("/funnel")
def get_conversion_funnel(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_agent = Depends(get_current_agent),
):
    """
    Get conversion funnel data.

    Funnel stages:
    - Property views
    - Leads captured
    - Contacts added
    - Contracts sent
    - Deals closed
    """
    service = AnalyticsService(db)
    funnel = service.get_conversion_funnel(current_agent.id, days)
    return {"funnel": funnel}


@router.get("/top-properties")
def get_top_properties(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_agent = Depends(get_current_agent),
):
    """
    Get most viewed properties.

    Useful for identifying popular listings.
    """
    service = AnalyticsService(db)
    top_properties = service.get_top_properties(current_agent.id, days, limit)
    return {"top_properties": top_properties}


@router.get("/traffic-sources")
def get_traffic_sources(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_agent = Depends(get_current_agent),
):
    """
    Get traffic breakdown by source.

    Shows where your traffic is coming from (direct, organic, social, etc.)
    """
    service = AnalyticsService(db)
    sources = service.get_traffic_sources(current_agent.id, days)
    return {"traffic_sources": sources}


@router.get("/geo-distribution")
def get_geo_distribution(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_agent = Depends(get_current_agent),
):
    """
    Get geographic distribution of leads.

    Shows breakdown by city.
    """
    service = AnalyticsService(db)
    geo = service.get_geo_distribution(current_agent.id, days)
    return {"geo_distribution": geo}


@router.get("/charts/{chart_type}")
def get_chart_data(
    chart_type: str,
    dimension: str = Query(..., description="Chart dimension"),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_agent = Depends(get_current_agent),
):
    """
    Get data for various chart types.

    Chart types:
    - line: Trends over time (property_views, leads_created, conversions)
    - pie: Distribution breakdowns (traffic_source, property_type, city)
    - bar: Comparisons (top_properties)

    Dimensions:
    - For line: property_views, leads_created, conversions
    - For pie: traffic_source, property_type, city
    - For bar: top_properties
    """
    service = AnalyticsService(db)
    chart_data = service.get_chart_data(current_agent.id, chart_type, dimension, days)
    return chart_data


@router.post("/track")
def track_event(
    event: EventTrackingSchema,
    request_data: dict,  # Will contain IP and user agent from request
    db: Session = Depends(get_db),
    current_agent = Depends(get_current_agent),
):
    """
    Track an analytics event.

    Use this to log user interactions for analytics.

    Event types:
    - property_view: User viewed a property
    - lead_created: New lead captured
    - conversion: Lead converted (scheduled showing, made offer)
    - page_view: User viewed a page
    - search: User performed a search
    - contact_form: User submitted contact form
    - custom: Any custom event

    Example:
    ```json
    {
        "event_type": "property_view",
        "event_name": "Property Details Viewed",
        "property_id": 123,
        "properties": {
            "source": "search",
            "referral": "google"
        }
    }
    ```
    """
    service = AnalyticsService.track_event(
        db=db,
        agent_id=current_agent.id,
        event_type=event.event_type,
        event_name=event.event_name,
        properties=event.properties,
        session_id=event.session_id,
        user_id=event.user_id,
        property_id=event.property_id,
        value=event.value,
        referrer=event.referrer,
        utm_source=event.utm_source,
        utm_medium=event.utm_medium,
        utm_campaign=event.utm_campaign,
        ip_address=request_data.get("ip_address"),
        user_agent=request_data.get("user_agent"),
    )

    return {"message": "Event tracked", "event_id": event.id}


# ============================================================
# Dashboard Management Endpoints
# ============================================================

@router.get("/dashboards")
def list_dashboards(
    db: Session = Depends(get_db),
    current_agent = Depends(get_current_agent),
):
    """
    Get all dashboards for the current agent.

    Returns both personal and public (team) dashboards.
    """
    dashboards = db.query(Dashboard).filter(
        or_(
            Dashboard.agent_id == current_agent.id,
            Dashboard.is_public == True
        )
    ).order_by(Dashboard.created_at.desc()).all()

    return {
        "dashboards": [dash.to_dict() for dash in dashboards]
    }


@router.post("/dashboards", status_code=201)
def create_dashboard(
    dashboard: DashboardCreateSchema,
    db: Session = Depends(get_db),
    current_agent = Depends(get_current_agent),
):
    """
    Create a new dashboard.

    Example:
    ```json
    {
        "name": "My Performance Dashboard",
        "description": "Track my key metrics",
        "layout": {
            "widgets": [
                {"id": "kpi-cards", "x": 0, "y": 0, "w": 12, "h": 2},
                {"id": "line-chart", "x": 0, "y": 2, "w": 8, "h": 4}
            ]
        },
        "widgets": {
            "kpi-cards": {
                "type": "kpi",
                "title": "Overview",
                "metrics": ["property_views", "leads", "conversions"]
            },
            "line-chart": {
                "type": "line",
                "title": "Property Views Over Time",
                "metric": "property_views"
            }
        }
    }
    ```
    """
    # If this is set as default, unset other defaults
    if dashboard.is_default:
        db.query(Dashboard).filter(
            and_(
                Dashboard.agent_id == current_agent.id,
                Dashboard.is_default == True
            )
        ).update({"is_default": False})

    new_dashboard = Dashboard(
        agent_id=current_agent.id,
        name=dashboard.name,
        description=dashboard.description,
        is_public=dashboard.is_public,
        layout=dashboard.layout,
        widgets=dashboard.widgets,
        filters=dashboard.filters,
        auto_refresh=dashboard.auto_refresh,
        refresh_interval_seconds=dashboard.refresh_interval_seconds,
        theme=dashboard.theme,
    )

    db.add(new_dashboard)
    db.commit()
    db.refresh(new_dashboard)

    return new_dashboard.to_dict()


@router.get("/dashboards/{dashboard_id}")
def get_dashboard(
    dashboard_id: int,
    db: Session = Depends(get_db),
    current_agent = Depends(get_current_agent),
):
    """Get a specific dashboard."""
    dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()

    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    # Check access
    if dashboard.agent_id != current_agent.id and not dashboard.is_public:
        raise HTTPException(status_code=403, detail="Access denied")

    return dashboard.to_dict()


@router.put("/dashboards/{dashboard_id}")
def update_dashboard(
    dashboard_id: int,
    dashboard: DashboardUpdateSchema,
    db: Session = Depends(get_db),
    current_agent = Depends(get_current_agent),
):
    """Update a dashboard."""
    dashboard_obj = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()

    if not dashboard_obj:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    if dashboard_obj.agent_id != current_agent.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Update fields
    if dashboard.name is not None:
        dashboard_obj.name = dashboard.name
    if dashboard.description is not None:
        dashboard_obj.description = dashboard.description
    if dashboard.is_public is not None:
        dashboard_obj.is_public = dashboard.is_public
    if dashboard.layout is not None:
        dashboard_obj.layout = dashboard.layout
    if dashboard.widgets is not None:
        dashboard_obj.widgets = dashboard.widgets
    if dashboard.filters is not None:
        dashboard_obj.filters = dashboard.filters
    if dashboard.auto_refresh is not None:
        dashboard_obj.auto_refresh = dashboard.auto_refresh
    if dashboard.refresh_interval_seconds is not None:
        dashboard_obj.refresh_interval_seconds = dashboard.refresh_interval_seconds
    if dashboard.theme is not None:
        dashboard_obj.theme = dashboard.theme

    db.commit()
    db.refresh(dashboard_obj)

    return dashboard_obj.to_dict()


@router.delete("/dashboards/{dashboard_id}")
def delete_dashboard(
    dashboard_id: int,
    db: Session = Depends(get_db),
    current_agent = Depends(get_current_agent),
):
    """Delete a dashboard."""
    dashboard_obj = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()

    if not dashboard_obj:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    if dashboard_obj.agent_id != current_agent.id:
        raise HTTPException(status_code=403, detail="Access denied")

    db.delete(dashboard_obj)
    db.commit()

    return {"message": "Dashboard deleted"}


# ============================================================
# Report Export Endpoints
# ============================================================

@router.get("/reports/performance")
def generate_performance_report(
    days: int = Query(30, ge=1, le=365),
    format: str = Query("json", pattern="^(json|pdf)$"),
    db: Session = Depends(get_db),
    current_agent = Depends(get_current_agent),
):
    """
    Generate a performance report.

    Includes:
    - Overview stats
    - Traffic trends
    - Conversion funnel
    - Top properties
    - Traffic sources
    - Geographic distribution

    Format options:
    - json: Return data as JSON
    - pdf: Generate PDF report (requires reportlab)
    """
    service = AnalyticsService(db)

    # Gather all data
    overview = service.get_dashboard_overview(current_agent.id, days)
    trend = service.get_events_trend(current_agent.id, "property_view", days)
    funnel = service.get_conversion_funnel(current_agent.id, days)
    top_properties = service.get_top_properties(current_agent.id, days)
    traffic_sources = service.get_traffic_sources(current_agent.id, days)
    geo_distribution = service.get_geo_distribution(current_agent.id, days)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "period_days": days,
        "agent_id": current_agent.id,
        "overview": overview,
        "trends": {"property_views_over_time": trend},
        "funnel": funnel,
        "top_properties": top_properties,
        "traffic_sources": traffic_sources,
        "geo_distribution": geo_distribution,
    }

    if format == "pdf":
        # Generate PDF (requires reportlab)
        try:
            from app.services.report_generator import ReportGenerator

            generator = ReportGenerator()
            pdf_bytes = generator.generate_performance_pdf(report)

            from fastapi.responses import Response
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=performance_report_{datetime.now(timezone.utc).strftime('%Y%m%d')}.pdf"
                },
            )
        except ImportError:
            raise HTTPException(
                status_code=501,
                detail="PDF generation not available. Install reportlab or use format=json"
            )
    else:
        return report


# ============================================================
# Widget Data Endpoints
# ============================================================

@router.get("/widgets/kpi")
def get_kpi_widget_data(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_agent = Depends(get_current_agent),
):
    """
    Get data for KPI cards widget.

    Returns overview stats in widget-friendly format.
    """
    service = AnalyticsService(db)
    stats = service.get_dashboard_overview(current_agent.id, days)

    return {
        "widget_type": "kpi_cards",
        "title": "Overview",
        "data": {
            "Property Views": stats["property_views"],
            "Leads Created": stats["leads_created"],
            "Conversions": stats["conversions"],
            "Conversion Rate": f"{stats['conversion_rate']}%",
            "Total Value": f"${stats['total_value_usd']:,.2f}",
            "Active Properties": stats["active_properties"],
            "New Properties": stats["new_properties"],
            "Contracts Signed": stats["contracts_signed"],
        },
        "period_days": days,
    }


@router.get("/widgets/line-chart")
def get_line_chart_widget_data(
    metric: str = Query("property_views", description="Metric to plot"),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_agent = Depends(get_current_agent),
):
    """
    Get data for line chart widget.

    Metrics: property_views, leads_created, conversions
    """
    service = AnalyticsService(db)
    chart_data = service._get_line_chart(current_agent.id, metric, days)

    return {
        "widget_type": "line_chart",
        "title": f"{metric.replace('_', ' ').title()} Over Time",
        "data": chart_data["data"],
    }


@router.get("/widgets/pie-chart")
def get_pie_chart_widget_data(
    dimension: str = Query("traffic_source", description="Data dimension"),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_agent = Depends(get_current_agent),
):
    """
    Get data for pie chart widget.

    Dimensions: traffic_source, property_type, city
    """
    service = AnalyticsService(db)
    chart_data = service._get_pie_chart(current_agent.id, dimension, days)

    return {
        "widget_type": "pie_chart",
        "title": f"{dimension.replace('_', ' ').title()} Distribution",
        "labels": chart_data["labels"],
        "values": chart_data["values"],
    }


@router.get("/widgets/bar-chart")
def get_bar_chart_widget_data(
    dimension: str = Query("top_properties", description="Data dimension"),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db),
    current_agent = Depends(get_current_agent),
):
    """
    Get data for bar chart widget.

    Dimensions: top_properties
    """
    service = AnalyticsService(db)
    chart_data = service._get_bar_chart(current_agent.id, dimension, days)

    return {
        "widget_type": "bar_chart",
        "title": f"{dimension.replace('_', ' ').title()}",
        "x": chart_data.get("x", []),
        "y": chart_data.get("y", []),
        "labels": chart_data.get("labels", []),
    }
