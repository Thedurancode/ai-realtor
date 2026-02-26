"""Market Watchlist Scanner - auto-import matching properties from Zillow."""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.market_watchlist import MarketWatchlist
from app.models.property import Property, PropertyStatus, PropertyType
from app.models.notification import Notification, NotificationPriority, NotificationType
from app.services.web_scraper_service import WebScraperService
from app.services.zillow_enrichment import ZillowEnrichmentService

logger = logging.getLogger(__name__)


class WatchlistScannerService:
    """Scan watchlists and auto-import matching properties from Zillow."""

    def __init__(self):
        self.scraper = WebScraperService()
        self.enrichment = ZillowEnrichmentService()

    def scan_all_watchlists(self, db: Session) -> Dict[str, Any]:
        """Scan all active watchlists and import matching properties.

        Returns:
            Dict with scan results: {watchlists_scanned, properties_found, properties_imported, notifications_created}
        """
        # Get all active watchlists
        watchlists = db.query(MarketWatchlist).filter(
            MarketWatchlist.is_active == True
        ).all()

        if not watchlists:
            logger.info("No active watchlists to scan")
            return {
                "watchlists_scanned": 0,
                "properties_found": 0,
                "properties_imported": 0,
                "notifications_created": 0,
                "results": []
            }

        results = []
        total_found = 0
        total_imported = 0
        total_notifications = 0

        for watchlist in watchlists:
            try:
                result = self.scan_watchlist(db, watchlist)
                results.append(result)
                total_found += result["properties_found"]
                total_imported += result["properties_imported"]
                total_notifications += result["notifications_created"]

                logger.info(
                    f"Watchlist '{watchlist.name}': {result['properties_found']} found, "
                    f"{result['properties_imported']} imported, "
                    f"{result['notifications_created']} notifications"
                )
            except Exception as e:
                logger.error(f"Error scanning watchlist {watchlist.id}: {e}")
                results.append({
                    "watchlist_id": watchlist.id,
                    "watchlist_name": watchlist.name,
                    "error": str(e),
                    "properties_found": 0,
                    "properties_imported": 0,
                    "notifications_created": 0
                })

        return {
            "watchlists_scanned": len(watchlists),
            "properties_found": total_found,
            "properties_imported": total_imported,
            "notifications_created": total_notifications,
            "scanned_at": datetime.now(timezone.utc).isoformat(),
            "results": results
        }

    def scan_watchlist(self, db: Session, watchlist: MarketWatchlist) -> Dict[str, Any]:
        """Scan a single watchlist and import matches.

        Args:
            db: Database session
            watchlist: Watchlist to scan

        Returns:
            Dict with scan results
        """
        criteria = watchlist.criteria or {}

        # Build Zillow search URL from criteria
        zillow_url = self._build_zillow_search_url(criteria)

        # Scrape Zillow search results
        properties_data = self._scrape_zillow_search(zillow_url)

        if not properties_data:
            return {
                "watchlist_id": watchlist.id,
                "watchlist_name": watchlist.name,
                "properties_found": 0,
                "properties_imported": 0,
                "notifications_created": 0
            }

        # Filter by exact criteria and check for duplicates
        new_properties = self._filter_and_dedupe(db, properties_data, criteria, watchlist.agent_id)

        # Import properties
        imported = []
        for prop_data in new_properties:
            try:
                prop = self._create_property(db, prop_data, watchlist.agent_id)
                imported.append(prop)

                logger.info(f"Imported property {prop.id}: {prop.address}")
            except Exception as e:
                logger.error(f"Error importing property: {e}")

        # Auto-enrich imported properties
        enriched_count = 0
        for prop in imported:
            try:
                self.enrichment.enrich_property(db, prop.id)
                enriched_count += 1
            except Exception as e:
                logger.error(f"Error enriching property {prop.id}: {e}")

        # Create notification for agent
        notification_count = 0
        if imported:
            notification = self._create_notification(
                db,
                watchlist.agent_id,
                watchlist,
                imported
            )
            notification_count = 1

        return {
            "watchlist_id": watchlist.id,
            "watchlist_name": watchlist.name,
            "properties_found": len(properties_data),
            "properties_imported": len(imported),
            "properties_enriched": enriched_count,
            "notifications_created": notification_count
        }

    def _build_zillow_search_url(self, criteria: Dict[str, Any]) -> str:
        """Build Zillow search URL from watchlist criteria.

        Args:
            criteria: Watchlist criteria dict

        Returns:
            Zillow search URL
        """
        # Base URL
        base_url = "https://www.zillow.com"

        # Build search path
        city = criteria.get("city", "").replace(" ", "-").lower()
        state = criteria.get("state", "").lower()

        path = f"/{city}-{state}/" if city and state else "/homes/"

        # Build query parameters
        params = []

        # Price range
        if criteria.get("min_price"):
            params.append(f"{criteria['min_price']}_price")
        if criteria.get("max_price"):
            params.append(f"{criteria['max_price']}_price")

        # Bedrooms
        if criteria.get("min_bedrooms"):
            params.append(f"{criteria['min_bedrooms']}_beds")

        # Bathrooms
        if criteria.get("min_bathrooms"):
            params.append(f"{criteria['min_bathrooms']}_baths")

        # Property type
        property_type = criteria.get("property_type")
        if property_type:
            type_map = {
                "house": "house",
                "condo": "condo",
                "townhouse": "townhouse",
                "apartment": "apartment",
                "land": "lot",
                "commercial": "comm"
            }
            if property_type.lower() in type_map:
                params.append(f"{type_map[property_type.lower()]}_type")

        # Square footage
        if criteria.get("min_sqft"):
            params.append(f"{criteria['min_sqft']}_size")

        # Combine params
        query_string = "_".join(params) if params else ""

        # Full URL
        url = f"{base_url}{path}{query_string}.html"
        return url

    def _scrape_zillow_search(self, zillow_url: str) -> List[Dict[str, Any]]:
        """Scrape Zillow search results page.

        Args:
            zillow_url: Zillow search URL

        Returns:
            List of property data dicts
        """
        try:
            # Use existing web scraper
            scrape_result = self.scraper.scrape_url(zillow_url, extract_properties=True)

            if scrape_result.get("properties"):
                return scrape_result["properties"]

            return []
        except Exception as e:
            logger.error(f"Error scraping Zillow search: {e}")
            return []

    def _filter_and_dedupe(
        self,
        db: Session,
        properties_data: List[Dict[str, Any]],
        criteria: Dict[str, Any],
        agent_id: int
    ) -> List[Dict[str, Any]]:
        """Filter properties by exact criteria and remove duplicates.

        Args:
            db: Database session
            properties_data: Scraped property data
            criteria: Watchlist criteria
            agent_id: Agent ID

        Returns:
            Filtered list of new properties
        """
        new_properties = []

        for prop_data in properties_data:
            # Check exact criteria match
            if not self._matches_criteria(prop_data, criteria):
                continue

            # Check for duplicates (by address)
            existing = db.query(Property).filter(
                Property.agent_id == agent_id,
                Property.address == prop_data.get("address")
            ).first()

            if existing:
                logger.debug(f"Property already exists: {prop_data.get('address')}")
                continue

            new_properties.append(prop_data)

        return new_properties

    def _matches_criteria(self, prop_data: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """Check if property matches watchlist criteria.

        Args:
            prop_data: Property data from scraper
            criteria: Watchlist criteria

        Returns:
            True if matches all criteria
        """
        # Price range
        price = prop_data.get("price", 0)
        if criteria.get("min_price") and price < criteria["min_price"]:
            return False
        if criteria.get("max_price") and price > criteria["max_price"]:
            return False

        # Bedrooms
        bedrooms = prop_data.get("bedrooms", 0)
        if criteria.get("min_bedrooms") and bedrooms < criteria["min_bedrooms"]:
            return False

        # Bathrooms
        bathrooms = prop_data.get("bathrooms", 0)
        if criteria.get("min_bathrooms") and bathrooms < criteria["min_bathrooms"]:
            return False

        # Square footage
        sqft = prop_data.get("square_feet", 0)
        if criteria.get("min_sqft") and sqft < criteria["min_sqft"]:
            return False

        # Property type
        if criteria.get("property_type"):
            prop_type = prop_data.get("property_type", "").lower()
            if criteria["property_type"].lower() not in prop_type:
                return False

        return True

    def _create_property(
        self,
        db: Session,
        prop_data: Dict[str, Any],
        agent_id: int
    ) -> Property:
        """Create property from scraped data.

        Args:
            db: Database session
            prop_data: Property data from scraper
            agent_id: Agent ID

        Returns:
            Created Property
        """
        prop = Property(
            agent_id=agent_id,
            title=prop_data.get("title", prop_data.get("address", "Property")),
            address=prop_data.get("address"),
            city=prop_data.get("city"),
            state=prop_data.get("state"),
            zip_code=prop_data.get("zip_code"),
            price=prop_data.get("price"),
            bedrooms=prop_data.get("bedrooms"),
            bathrooms=prop_data.get("bathrooms"),
            square_feet=prop_data.get("square_feet"),
            year_built=prop_data.get("year_built"),
            lot_size=prop_data.get("lot_size"),
            property_type=self._parse_property_type(prop_data.get("property_type")),
            status=PropertyStatus.NEW_PROPERTY,
            description=prop_data.get("description"),
            source="watchlist_auto_import"
        )

        db.add(prop)
        db.commit()
        db.refresh(prop)

        return prop

    def _parse_property_type(self, property_type: Optional[str]) -> PropertyType:
        """Parse property type string to enum.

        Args:
            property_type: Property type string

        Returns:
            PropertyType enum
        """
        if not property_type:
            return PropertyType.HOUSE

        type_lower = property_type.lower()

        type_map = {
            "house": PropertyType.HOUSE,
            "single family": PropertyType.HOUSE,
            "condo": PropertyType.CONDO,
            "condominium": PropertyType.CONDO,
            "townhouse": PropertyType.TOWNHOUSE,
            "apartment": PropertyType.APARTMENT,
            "land": PropertyType.LAND,
            "lot": PropertyType.LAND,
            "commercial": PropertyType.COMMERCIAL
        }

        for key, value in type_map.items():
            if key in type_lower:
                return value

        return PropertyType.HOUSE

    def _create_notification(
        self,
        db: Session,
        agent_id: int,
        watchlist: MarketWatchlist,
        properties: List[Property]
    ) -> Notification:
        """Create notification for imported properties.

        Args:
            db: Database session
            agent_id: Agent ID
            watchlist: Watchlist that matched
            properties: Imported properties

        Returns:
            Created Notification
        """
        prop_summary = "\n".join([
            f"• {p.address} - ${p.price:,.0f} ({p.bedrooms} bed, {p.bathrooms} bath)"
            for p in properties[:5]  # Limit to first 5
        ])

        if len(properties) > 5:
            prop_summary += f"\n• ... and {len(properties) - 5} more"

        title = f"🎯 {len(properties)} New Properties Found!"
        message = f"""Your watchlist '{watchlist.name}' found {len(properties)} new matching properties:

{prop_summary}

All properties have been imported and enriched with Zillow data.
"""

        notification = Notification(
            agent_id=agent_id,
            type=NotificationType.SYSTEM,
            priority=NotificationPriority.HIGH,
            title=title,
            message=message,
            metadata={
                "watchlist_id": watchlist.id,
                "watchlist_name": watchlist.name,
                "property_count": len(properties),
                "property_ids": [p.id for p in properties],
                "source": "watchlist_scanner"
            }
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        return notification


watchlist_scanner_service = WatchlistScannerService()
