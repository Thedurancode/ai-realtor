"""SQLite Tuning API router.

Provides endpoints for monitoring and optimizing SQLite performance.
"""

from fastapi import APIRouter
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.database import get_db
from app.services.sqlite_tuning import sqlite_tuner, SQLiteIndexAnalyzer
from app.database import engine


router = APIRouter(prefix="/sqlite", tags=["SQLite Tuning"])


@router.get("/stats")
async def get_sqlite_stats():
    """Get SQLite performance statistics.

    Returns:
        - queries_executed: Total number of queries
        - total_query_time: Total time spent executing queries (seconds)
        - average_query_time: Average query time (seconds)
        - slow_queries: List of queries exceeding threshold
        - optimizations_applied: List of PRAGMA optimizations applied
    """
    return sqlite_tuner.get_stats()


@router.get("/slow-queries")
async def get_slow_queries(limit: int = 50):
    """Get slow queries.

    Returns queries that exceeded the slow query threshold (100ms).
    """
    return {
        "total_slow_queries": len(sqlite_tuner.stats["slow_queries"]),
        "slow_queries": sqlite_tuner.get_slow_queries(limit=limit)
    }


@router.post("/stats/reset")
async def reset_sqlite_stats():
    """Reset performance statistics."""
    sqlite_tuner.reset_stats()

    return {
        "status": "reset"
    }


@router.get("/optimizations")
async def get_optimizations():
    """Get list of optimizations applied."""
    return {
        "optimizations_applied": sqlite_tuner.optimizations_applied
    }


@router.post("/optimize")
async def apply_optimizations():
    """Apply SQLite performance optimizations.

    Optimizations:
    - WAL mode (Write-Ahead Logging)
    - Synchronous mode = NORMAL
    - Cache size = 64MB
    - Temp store = MEMORY
    - Memory map I/O = 256MB
    - Page size = 4096
    - Busy timeout = 5000ms
    """
    # Clear previous optimizations
    sqlite_tuner.optimizations_applied = []

    # Apply optimizations
    sqlite_tuner.apply_optimizations(engine)

    return {
        "status": "optimized",
        "optimizations_applied": sqlite_tuner.optimizations_applied
    }


@router.get("/index-suggestions")
async def get_index_suggestions():
    """Analyze and suggest missing indexes.

    Returns:
        List of suggested indexes for common query patterns.
    """
    analyzer = SQLiteIndexAnalyzer(engine)

    suggestions = analyzer.analyze_missing_indexes()

    return {
        "total_suggestions": len(suggestions),
        "suggestions": suggestions
    }


@router.get("/table-stats")
async def get_table_stats():
    """Get table statistics.

    Returns row counts for all tables.
    """
    analyzer = SQLiteIndexAnalyzer(engine)

    stats = analyzer.get_table_stats()

    return {
        "total_tables": len(stats),
        "tables": stats
    }


@router.get("/performance-report")
async def get_performance_report():
    """Get comprehensive performance report.

    Combines stats, slow queries, and optimization status.
    """
    stats = sqlite_tuner.get_stats()
    slow_queries = sqlite_tuner.get_slow_queries(limit=10)

    return {
        "statistics": {
            "queries_executed": stats["queries_executed"],
            "total_query_time": stats["total_query_time"],
            "average_query_time": stats["average_query_time"]
        },
        "slow_queries": {
            "total": len(stats["slow_queries"]),
            "top_10": slow_queries
        },
        "optimizations": {
            "total_applied": len(stats["optimizations_applied"]),
            "optimizations": stats["optimizations_applied"]
        },
        "threshold": {
            "slow_query_seconds": sqlite_tuner.slow_query_threshold
        }
    }
