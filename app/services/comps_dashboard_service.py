"""Comparable Sales Dashboard — aggregates comp data from multiple sources."""

from datetime import datetime, timezone
from statistics import mean, median
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.property import Property, PropertyStatus
from app.models.zillow_enrichment import ZillowEnrichment


class CompsDashboardService:
    """Aggregate comp sales, rentals, and internal portfolio into a unified analysis."""

    MARKET_TOLERANCE_PCT = 5.0  # within 5% = "at_market"

    # ── Public API ──

    def get_dashboard(self, db: Session, property_id: int) -> dict:
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            raise ValueError(f"Property {property_id} not found")

        enrichment = db.query(ZillowEnrichment).filter(ZillowEnrichment.property_id == property_id).first()
        zestimate = enrichment.zestimate if enrichment else None
        rent_zestimate = enrichment.rent_zestimate if enrichment else None

        subject = self._build_subject(prop, zestimate, rent_zestimate)

        # Load comps from all sources
        rp = self._find_research_property(db, prop)
        research_sales = self._load_comp_sales(db, rp.id) if rp else []
        research_rentals = self._load_comp_rentals(db, rp.id) if rp else []
        zillow_sales = self._load_zillow_sold_history(enrichment)
        internal_comps = self._load_internal_portfolio_comps(db, prop)

        all_sales = research_sales + zillow_sales
        all_sales.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)

        metrics = self._compute_market_metrics(all_sales, prop.price, zestimate)
        rental_metrics = self._compute_rental_metrics(research_rentals)
        recommendation = self._build_pricing_recommendation(metrics, prop.price, zestimate)
        voice = self._build_voice_summary(subject, metrics, len(all_sales), len(research_rentals))

        return {
            "property_id": property_id,
            "subject": subject,
            "comp_sales": all_sales[:20],
            "comp_rentals": research_rentals[:20],
            "internal_portfolio_comps": internal_comps[:10],
            "market_metrics": {**metrics, **rental_metrics},
            "pricing_recommendation": recommendation,
            "data_sources": {
                "comp_sales_from_research": len(research_sales),
                "comp_sales_from_zillow": len(zillow_sales),
                "comp_rentals": len(research_rentals),
                "internal_portfolio": len(internal_comps),
                "has_zillow_enrichment": enrichment is not None,
                "has_agentic_research": rp is not None,
            },
            "voice_summary": voice,
        }

    def get_sales(self, db: Session, property_id: int) -> dict:
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            raise ValueError(f"Property {property_id} not found")

        enrichment = db.query(ZillowEnrichment).filter(ZillowEnrichment.property_id == property_id).first()
        zestimate = enrichment.zestimate if enrichment else None
        subject = self._build_subject(prop, zestimate, enrichment.rent_zestimate if enrichment else None)

        rp = self._find_research_property(db, prop)
        research_sales = self._load_comp_sales(db, rp.id) if rp else []
        zillow_sales = self._load_zillow_sold_history(enrichment)

        all_sales = research_sales + zillow_sales
        all_sales.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)

        metrics = self._compute_market_metrics(all_sales, prop.price, zestimate)
        recommendation = self._build_pricing_recommendation(metrics, prop.price, zestimate)

        parts = [f"Property has {len(all_sales)} comparable sale{'s' if len(all_sales) != 1 else ''}."]
        if metrics.get("median_sale_price"):
            parts.append(f"Median comp price: ${metrics['median_sale_price']:,.0f}.")
        if metrics.get("subject_vs_market") and metrics["subject_vs_market"] != "at_market":
            parts.append(f"Listed {abs(metrics.get('subject_difference_pct', 0)):.0f}% {metrics['subject_vs_market'].replace('_', ' ')}.")
        voice = " ".join(parts) if parts else "No sales comp data available."

        return {
            "property_id": property_id,
            "subject": subject,
            "comp_sales": all_sales[:20],
            "market_metrics": metrics,
            "pricing_recommendation": recommendation,
            "voice_summary": voice,
        }

    def get_rentals(self, db: Session, property_id: int) -> dict:
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            raise ValueError(f"Property {property_id} not found")

        enrichment = db.query(ZillowEnrichment).filter(ZillowEnrichment.property_id == property_id).first()
        rent_zestimate = enrichment.rent_zestimate if enrichment else None
        subject = self._build_subject(prop, enrichment.zestimate if enrichment else None, rent_zestimate)

        rp = self._find_research_property(db, prop)
        rentals = self._load_comp_rentals(db, rp.id) if rp else []
        rental_metrics = self._compute_rental_metrics(rentals)

        parts = [f"Property has {len(rentals)} comparable rental{'s' if len(rentals) != 1 else ''}."]
        if rental_metrics.get("median_rent"):
            parts.append(f"Median rent: ${rental_metrics['median_rent']:,.0f}/mo.")
        if rent_zestimate:
            parts.append(f"Zillow Rent Zestimate: ${rent_zestimate:,.0f}/mo.")
        voice = " ".join(parts) if parts else "No rental comp data available."

        return {
            "property_id": property_id,
            "subject": subject,
            "comp_rentals": rentals[:20],
            "rental_metrics": rental_metrics,
            "voice_summary": voice,
        }

    # ── Subject ──

    def _build_subject(self, prop: Property, zestimate, rent_zestimate) -> dict:
        return {
            "address": f"{prop.address}, {prop.city}, {prop.state}",
            "city": prop.city,
            "state": prop.state,
            "price": prop.price,
            "beds": prop.bedrooms,
            "baths": prop.bathrooms,
            "sqft": prop.square_feet,
            "property_type": prop.property_type.value if prop.property_type else None,
            "zestimate": zestimate,
            "rent_zestimate": rent_zestimate,
        }

    # ── Data loaders ──

    def _find_research_property(self, db: Session, prop: Property):
        try:
            from app.models.agentic_property import ResearchProperty
            return (
                db.query(ResearchProperty)
                .filter(
                    or_(
                        ResearchProperty.normalized_address.ilike(f"%{prop.address}%"),
                        ResearchProperty.raw_address.ilike(f"%{prop.address}%"),
                    )
                )
                .first()
            )
        except Exception:
            return None

    def _load_comp_sales(self, db: Session, rp_id: int) -> list[dict]:
        try:
            from app.models.comp_sale import CompSale
            rows = (
                db.query(CompSale)
                .filter(CompSale.research_property_id == rp_id)
                .order_by(CompSale.similarity_score.desc())
                .limit(20)
                .all()
            )
            return [
                {
                    "address": r.address,
                    "sale_price": r.sale_price,
                    "sale_date": r.sale_date.isoformat() if r.sale_date else None,
                    "distance_mi": r.distance_mi,
                    "sqft": r.sqft,
                    "beds": r.beds,
                    "baths": r.baths,
                    "year_built": r.year_built,
                    "similarity_score": round(r.similarity_score, 2),
                    "source": "agentic_research",
                    "source_url": r.source_url,
                }
                for r in rows
            ]
        except Exception:
            return []

    def _load_comp_rentals(self, db: Session, rp_id: int) -> list[dict]:
        try:
            from app.models.comp_rental import CompRental
            rows = (
                db.query(CompRental)
                .filter(CompRental.research_property_id == rp_id)
                .order_by(CompRental.similarity_score.desc())
                .limit(20)
                .all()
            )
            return [
                {
                    "address": r.address,
                    "rent": r.rent,
                    "date_listed": r.date_listed.isoformat() if r.date_listed else None,
                    "distance_mi": r.distance_mi,
                    "sqft": r.sqft,
                    "beds": r.beds,
                    "baths": r.baths,
                    "similarity_score": round(r.similarity_score, 2),
                    "source_url": r.source_url,
                }
                for r in rows
            ]
        except Exception:
            return []

    def _load_zillow_sold_history(self, enrichment: Optional[ZillowEnrichment]) -> list[dict]:
        if not enrichment or not enrichment.price_history:
            return []

        history = enrichment.price_history
        if not isinstance(history, list):
            return []

        sales = []
        for entry in history:
            if not isinstance(entry, dict):
                continue
            event = str(entry.get("event", "")).lower()
            if "sold" not in event:
                continue
            price = entry.get("price")
            if not price:
                continue
            sales.append({
                "address": entry.get("address", "Subject property (historical)"),
                "sale_price": float(price),
                "sale_date": entry.get("date"),
                "distance_mi": 0.0,
                "sqft": entry.get("sqft"),
                "beds": entry.get("beds"),
                "baths": entry.get("baths"),
                "year_built": None,
                "similarity_score": 0.5,  # Lower score for historical self-sales
                "source": "zillow_price_history",
                "source_url": None,
            })
        return sales

    def _load_internal_portfolio_comps(self, db: Session, prop: Property) -> list[dict]:
        candidates = (
            db.query(Property)
            .filter(
                Property.id != prop.id,
                Property.city == prop.city,
                Property.state == prop.state,
                Property.status.in_([PropertyStatus.NEW_PROPERTY, PropertyStatus.ENRICHED, PropertyStatus.RESEARCHED, PropertyStatus.WAITING_FOR_CONTRACTS, PropertyStatus.COMPLETE]),
            )
            .limit(50)
            .all()
        )

        scored = []
        for c in candidates:
            score = self._simple_similarity(prop, c)
            if score >= 0.3:
                scored.append({
                    "property_id": c.id,
                    "address": f"{c.address}, {c.city}",
                    "city": c.city,
                    "price": c.price,
                    "beds": c.bedrooms,
                    "baths": c.bathrooms,
                    "sqft": c.square_feet,
                    "status": c.status.value if c.status else "unknown",
                    "similarity_score": round(score, 2),
                })

        scored.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored[:10]

    def _simple_similarity(self, subject: Property, candidate: Property) -> float:
        score = 0.0
        total_weight = 0.0

        # Price similarity (40%)
        if subject.price and candidate.price and subject.price > 0:
            price_ratio = min(subject.price, candidate.price) / max(subject.price, candidate.price)
            score += 0.4 * price_ratio
            total_weight += 0.4

        # Bedroom match (20%)
        if subject.bedrooms is not None and candidate.bedrooms is not None:
            diff = abs(subject.bedrooms - candidate.bedrooms)
            score += 0.2 * max(0, 1 - diff / 3)
            total_weight += 0.2

        # Bathroom match (10%)
        if subject.bathrooms is not None and candidate.bathrooms is not None:
            diff = abs(subject.bathrooms - candidate.bathrooms)
            score += 0.1 * max(0, 1 - diff / 3)
            total_weight += 0.1

        # Square footage match (30%)
        if subject.square_feet and candidate.square_feet and subject.square_feet > 0:
            sqft_ratio = min(subject.square_feet, candidate.square_feet) / max(subject.square_feet, candidate.square_feet)
            score += 0.3 * sqft_ratio
            total_weight += 0.3

        return score / total_weight if total_weight > 0 else 0.0

    # ── Market metrics ──

    def _compute_market_metrics(self, sales: list[dict], subject_price: float, zestimate: Optional[float]) -> dict:
        prices = [s["sale_price"] for s in sales if s.get("sale_price")]
        ppsf_list = [
            s["sale_price"] / s["sqft"]
            for s in sales
            if s.get("sale_price") and s.get("sqft") and s["sqft"] > 0
        ]

        if not prices:
            return {
                "comp_count": 0,
                "avg_sale_price": None,
                "median_sale_price": None,
                "avg_price_per_sqft": None,
                "median_price_per_sqft": None,
                "price_range": None,
                "price_trend": "insufficient_data",
                "trend_pct": None,
                "subject_vs_market": None,
                "subject_difference_pct": None,
                "zestimate_vs_comps": None,
            }

        avg_price = mean(prices)
        med_price = median(prices)
        avg_ppsf = mean(ppsf_list) if ppsf_list else None
        med_ppsf = median(ppsf_list) if ppsf_list else None

        # Price trend
        trend, trend_pct = self._compute_price_trend(sales)

        # Subject vs market
        subject_vs, diff_pct = self._compare_to_market(subject_price, med_price)

        # Zestimate vs comps
        zest_comp = None
        if zestimate and avg_price:
            diff = zestimate - avg_price
            zest_comp = {
                "zestimate": zestimate,
                "comp_avg": round(avg_price),
                "difference": round(diff),
                "difference_pct": round(diff / avg_price * 100, 1) if avg_price else None,
            }

        return {
            "comp_count": len(prices),
            "avg_sale_price": round(avg_price),
            "median_sale_price": round(med_price),
            "avg_price_per_sqft": round(avg_ppsf) if avg_ppsf else None,
            "median_price_per_sqft": round(med_ppsf) if med_ppsf else None,
            "price_range": {"min": min(prices), "max": max(prices)},
            "price_trend": trend,
            "trend_pct": trend_pct,
            "subject_vs_market": subject_vs,
            "subject_difference_pct": diff_pct,
            "zestimate_vs_comps": zest_comp,
        }

    def _compute_rental_metrics(self, rentals: list[dict]) -> dict:
        rents = [r["rent"] for r in rentals if r.get("rent")]
        if not rents:
            return {"avg_rent": None, "median_rent": None, "rent_range": None, "rent_count": 0}

        return {
            "avg_rent": round(mean(rents)),
            "median_rent": round(median(rents)),
            "rent_range": {"min": min(rents), "max": max(rents)},
            "rent_count": len(rents),
        }

    def _compute_price_trend(self, sales: list[dict]) -> tuple[str, Optional[float]]:
        dated = [(s["sale_date"], s["sale_price"]) for s in sales if s.get("sale_date") and s.get("sale_price")]
        if len(dated) < 3:
            return "insufficient_data", None

        # Sort by date
        dated.sort(key=lambda x: str(x[0]))

        # Split into halves (older vs newer)
        mid = len(dated) // 2
        older_avg = mean([p for _, p in dated[:mid]])
        newer_avg = mean([p for _, p in dated[mid:]])

        if older_avg == 0:
            return "stable", 0.0

        change_pct = round((newer_avg - older_avg) / older_avg * 100, 1)

        if change_pct > 2:
            return "appreciating", change_pct
        elif change_pct < -2:
            return "depreciating", change_pct
        return "stable", change_pct

    def _compare_to_market(self, subject_price: float, median_price: float) -> tuple[Optional[str], Optional[float]]:
        if not subject_price or not median_price:
            return None, None

        diff_pct = round((subject_price - median_price) / median_price * 100, 1)

        if abs(diff_pct) <= self.MARKET_TOLERANCE_PCT:
            return "at_market", diff_pct
        elif diff_pct > 0:
            return "above_market", diff_pct
        return "below_market", diff_pct

    # ── Recommendation ──

    def _build_pricing_recommendation(self, metrics: dict, subject_price: float, zestimate: Optional[float]) -> str:
        comp_count = metrics.get("comp_count", 0)
        med_price = metrics.get("median_sale_price")

        if comp_count == 0:
            rec = "No comparable sales data available. Recommend enriching with Zillow and running agentic research."
            if zestimate:
                rec += f" Zillow Zestimate is ${zestimate:,.0f}."
            return rec

        parts = []
        if comp_count >= 5:
            parts.append(f"Based on {comp_count} comparable sales, estimated market value is ${med_price:,.0f}.")
        else:
            parts.append(f"Limited comp data ({comp_count} sale{'s' if comp_count != 1 else ''}). Median: ${med_price:,.0f}. Consider running agentic research for more data.")

        diff_pct = metrics.get("subject_difference_pct")
        vs = metrics.get("subject_vs_market")
        if vs and diff_pct is not None and vs != "at_market":
            label = "above" if vs == "above_market" else "below"
            parts.append(f"List price of ${subject_price:,.0f} is {abs(diff_pct):.0f}% {label} market.")
        elif vs == "at_market":
            parts.append(f"List price of ${subject_price:,.0f} is in line with the market.")

        zest = metrics.get("zestimate_vs_comps")
        if zest and zest.get("difference_pct") is not None:
            label = "above" if zest["difference_pct"] > 0 else "below"
            parts.append(f"Zestimate (${zest['zestimate']:,.0f}) is {abs(zest['difference_pct']):.0f}% {label} comp average.")

        return " ".join(parts)

    # ── Voice summary ──

    def _build_voice_summary(self, subject: dict, metrics: dict, comp_count: int, rental_count: int) -> str:
        if comp_count == 0 and rental_count == 0:
            return "No comparable sales or rental data available for this property. Consider running agentic research."

        parts = []
        addr = subject["address"].split(",")[0]

        if comp_count > 0:
            parts.append(f"{addr} has {comp_count} comparable sale{'s' if comp_count != 1 else ''}.")
            med = metrics.get("median_sale_price")
            if med:
                parts.append(f"Median comp price is ${med:,.0f}.")
            diff = metrics.get("subject_difference_pct")
            vs = metrics.get("subject_vs_market")
            if vs and diff is not None and vs != "at_market":
                label = "above" if vs == "above_market" else "below"
                parts.append(f"Your list price is {abs(diff):.0f}% {label} market.")
            trend = metrics.get("price_trend")
            trend_pct = metrics.get("trend_pct")
            if trend and trend not in ("stable", "insufficient_data") and trend_pct:
                parts.append(f"Market is {trend} at {abs(trend_pct):.1f}%.")

        if rental_count > 0:
            med_rent = metrics.get("median_rent")
            if med_rent:
                parts.append(f"{rental_count} rental comp{'s' if rental_count != 1 else ''}, median ${med_rent:,.0f}/mo.")

        return " ".join(parts)


comps_dashboard_service = CompsDashboardService()
