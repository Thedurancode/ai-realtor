"""Cron handler for watchlist scanner - auto-scan watchlists periodically."""
import logging
from sqlalchemy.orm import Session

from app.session import SessionLocal
from app.services.watchlist_scanner_service import watchlist_scanner_service

logger = logging.getLogger(__name__)


async def handle_watchlist_scan(metadata: dict = None):
    """Cron handler: Scan all active watchlists for new properties.

    This runs every N hours (configured in cron scheduler) and:
    1. Scrapes Zillow for each watchlist
    2. Imports new matching properties
    3. Auto-enriches with Zillow data
    4. Creates notifications for agents

    Usage:
        await cron_scheduler.schedule_task(
            name="watchlist_scanner",
            handler_name="watchlist_scanner",
            cron_expression="0 */6 * * *"  # Every 6 hours
        )
    """
    db = SessionLocal()
    try:
        logger.info("Starting watchlist scanner...")

        results = watchlist_scanner_service.scan_all_watchlists(db)

        logger.info(
            f"Watchlist scanner completed: "
            f"{results['watchlists_scanned']} watchlists, "
            f"{results['properties_found']} found, "
            f"{results['properties_imported']} imported, "
            f"{results['notifications_created']} notifications"
        )

        return results

    except Exception as e:
        logger.error(f"Watchlist scanner failed: {e}")
        raise
    finally:
        db.close()
