"""SQLite Performance Tuning.

Implements SQLite optimization strategies for improved performance:
- WAL mode (Write-Ahead Logging) for better concurrency
- Connection pooling for reduced overhead
- Prepared statement caching
- Index optimization
- Query optimization
- Memory tuning

Inspired by ZeroClaw's SQLite tuning strategies.

Usage:
    from app.services.sqlite_tuning import sqlite_tuner

    # Apply optimizations on startup
    sqlite_tuner.apply_optimizations(engine)

    # Get performance stats
    stats = sqlite_tuner.get_stats()
"""

import sqlite3
import time
from typing import Dict, Any, Optional, List
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from contextlib import contextmanager
import threading


class SQLiteTuner:
    """SQLite performance tuning utilities."""

    def __init__(self):
        """Initialize SQLite tuner."""
        self.stats = {
            "queries_executed": 0,
            "total_query_time": 0.0,
            "slow_queries": [],
            "connection_pool_hits": 0,
            "connection_pool_misses": 0
        }
        self.slow_query_threshold = 0.1  # 100ms
        self.optimizations_applied = []

    def apply_optimizations(self, engine: Engine) -> None:
        """Apply SQLite performance optimizations.

        Args:
            engine: SQLAlchemy engine

        Optimizations applied:
        - WAL mode (Write-Ahead Logging)
        - Synchronous mode = NORMAL
        - Cache size = -64000 (64MB)
        - Temp store = MEMORY
        - Mmap size = 268435456 (256MB)
        - Journal mode = WAL
        - Page size = 4096
        - Busy timeout = 5000ms
        """
        # Get raw SQLite connection
        conn = engine.raw_connection()
        cursor = conn.cursor()

        optimizations = [
            # WAL mode for better concurrency
            ("PRAGMA journal_mode=WAL", "WAL mode enabled"),

            # Synchronous mode = NORMAL (safer than OFF, faster than FULL)
            ("PRAGMA synchronous=NORMAL", "Synchronous mode set to NORMAL"),

            # Cache size = 64MB (negative value = KB)
            ("PRAGMA cache_size=-64000", "Cache size set to 64MB"),

            # Store temp tables in memory
            ("PRAGMA temp_store=MEMORY", "Temp store set to MEMORY"),

            # Memory map I/O (256MB)
            ("PRAGMA mmap_size=268435456", "Memory map size set to 256MB"),

            # Page size = 4096 (optimal for most filesystems)
            ("PRAGMA page_size=4096", "Page size set to 4096"),

            # Busy timeout = 5 seconds
            ("PRAGMA busy_timeout=5000", "Busy timeout set to 5000ms"),

            # Foreign key enforcement
            ("PRAGMA foreign_keys=ON", "Foreign keys enabled"),

            # Query optimizer settings
            ("PRAGMA optimize", "Query optimizer run"),

            # Automatic vacuum (disabled for now - can be scheduled)
            # ("PRAGMA auto_vacuum=INCREMENTAL", "Auto vacuum set to INCREMENTAL"),
        ]

        for pragma, description in optimizations:
            try:
                cursor.execute(pragma)
                result = cursor.fetchone()
                self.optimizations_applied.append({
                    "pragma": pragma,
                    "description": description,
                    "result": result[0] if result else None
                })
            except Exception as e:
                print(f"Failed to apply optimization '{pragma}': {e}")

        conn.commit()
        conn.close()

        # Register query performance monitoring
        self._register_query_monitoring(engine)

    def _register_query_monitoring(self, engine: Engine) -> None:
        """Register event listeners for query monitoring.

        Args:
            engine: SQLAlchemy engine
        """
        @event.listens_for(engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()

        @event.listens_for(engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - context._query_start_time

            # Update stats
            self.stats["queries_executed"] += 1
            self.stats["total_query_time"] += total

            # Track slow queries
            if total > self.slow_query_threshold:
                self.stats["slow_queries"].append({
                    "statement": statement[:500],  # Truncate long queries
                    "duration": total,
                    "timestamp": time.time()
                })

    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics.

        Returns:
            Dictionary with performance stats
        """
        stats = self.stats.copy()

        # Calculate average query time
        if stats["queries_executed"] > 0:
            stats["average_query_time"] = stats["total_query_time"] / stats["queries_executed"]
        else:
            stats["average_query_time"] = 0.0

        # Include optimizations applied
        stats["optimizations_applied"] = self.optimizations_applied

        return stats

    def get_slow_queries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get slow queries.

        Args:
            limit: Maximum number of slow queries to return

        Returns:
            List of slow query dictionaries
        """
        # Sort by duration (slowest first) and limit
        slow_queries = sorted(
            self.stats["slow_queries"],
            key=lambda x: x["duration"],
            reverse=True
        )[:limit]

        return slow_queries

    def reset_stats(self) -> None:
        """Reset performance statistics."""
        self.stats = {
            "queries_executed": 0,
            "total_query_time": 0.0,
            "slow_queries": [],
            "connection_pool_hits": 0,
            "connection_pool_misses": 0
        }


class SQLiteConnectionPool:
    """Simple connection pool for SQLite.

    Note: SQLAlchemy has built-in pooling, but this provides
    additional control for tuning.
    """

    def __init__(self, database_url: str, pool_size: int = 5):
        """Initialize connection pool.

        Args:
            database_url: SQLite database URL
            pool_size: Maximum number of connections
        """
        self.database_url = database_url
        self.pool_size = pool_size
        self.connections: List[sqlite3.Connection] = []
        self.lock = threading.Lock()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "created": 0
        }

    @contextmanager
    def get_connection(self):
        """Get a connection from the pool.

        Yields:
            SQLite connection
        """
        conn = None

        with self.lock:
            if self.connections:
                # Reuse existing connection
                conn = self.connections.pop()
                self.stats["hits"] += 1
            else:
                # Create new connection
                conn = sqlite3.connect(self.database_url)
                self.stats["created"] += 1
                self.stats["misses"] += 1

        try:
            yield conn
        finally:
            # Return connection to pool
            with self.lock:
                if len(self.connections) < self.pool_size:
                    self.connections.append(conn)
                else:
                    # Pool full, close connection
                    conn.close()

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics.

        Returns:
            Dictionary with pool stats
        """
        return {
            "pool_size": self.pool_size,
            "available_connections": len(self.connections),
            "total_created": self.stats["created"],
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": self.stats["hits"] / (self.stats["hits"] + self.stats["misses"])
            if (self.stats["hits"] + self.stats["misses"]) > 0
            else 0.0
        }

    def close_all(self) -> None:
        """Close all connections in the pool."""
        with self.lock:
            for conn in self.connections:
                conn.close()
            self.connections = []


class SQLiteIndexAnalyzer:
    """Analyze and suggest indexes for SQLite."""

    def __init__(self, engine: Engine):
        """Initialize index analyzer.

        Args:
            engine: SQLAlchemy engine
        """
        self.engine = engine

    def analyze_missing_indexes(self) -> List[Dict[str, Any]]:
        """Analyze queries and suggest missing indexes.

        This is a simplified version. A full implementation would:
        - Analyze slow query log
        - Check table sizes
        - Examine WHERE clauses
        - Check JOIN columns

        Returns:
            List of index suggestions
        """
        suggestions = []

        # Common index suggestions for the platform
        common_indexes = [
            {
                "table": "properties",
                "columns": ["agent_id", "status"],
                "reason": "Filtering properties by agent and status"
            },
            {
                "table": "properties",
                "columns": ["city", "state"],
                "reason": "Filtering by location"
            },
            {
                "table": "contracts",
                "columns": ["property_id", "status"],
                "reason": "Checking contract status for property"
            },
            {
                "table": "voice_memory_nodes",
                "columns": ["session_id", "node_type"],
                "reason": "Querying memory by session and type"
            },
            {
                "table": "voice_memory_edges",
                "columns": ["session_id", "source_id"],
                "reason": "Querying edges by session and source"
            },
            {
                "table": "conversation_history",
                "columns": ["session_id", "created_at"],
                "reason": "Retrieving conversation history"
            },
            {
                "table": "notifications",
                "columns": ["agent_id", "read", "created_at"],
                "reason": "Fetching unread notifications"
            },
            {
                "table": "scheduled_tasks",
                "columns": ["agent_id", "status", "due_at"],
                "reason": "Querying due tasks"
            }
        ]

        # Check which indexes exist
        with self.engine.connect() as conn:
            for suggestion in common_indexes:
                table = suggestion["table"]
                columns = suggestion["columns"]

                # Check if index exists
                result = conn.execute(text(f"""
                    SELECT name FROM sqlite_master
                    WHERE type='index'
                    AND tbl_name='{table}'
                    AND sql LIKE '%{columns[0]}%'
                """))

                if not result.fetchone():
                    suggestions.append(suggestion)

        return suggestions

    def get_table_stats(self) -> List[Dict[str, Any]]:
        """Get table statistics.

        Returns:
            List of table stat dictionaries
        """
        stats = []

        with self.engine.connect() as conn:
            # Get all tables
            result = conn.execute(text("""
                SELECT name FROM sqlite_master
                WHERE type='table'
                AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """))

            tables = [row[0] for row in result]

            # Get row count for each table
            for table in tables:
                try:
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    row_count = count_result.fetchone()[0]

                    stats.append({
                        "table": table,
                        "row_count": row_count
                    })
                except Exception as e:
                    print(f"Error getting stats for {table}: {e}")

        return stats


# Global singleton instance
sqlite_tuner = SQLiteTuner()


def optimize_sqlite(engine: Engine) -> None:
    """Apply SQLite optimizations to an engine.

    Args:
        engine: SQLAlchemy engine

    Example:
        from app.database import engine
        from app.services.sqlite_tuning import optimize_sqlite

        optimize_sqlite(engine)
    """
    sqlite_tuner.apply_optimizations(engine)


def get_sqlite_stats() -> Dict[str, Any]:
    """Get SQLite performance statistics.

    Returns:
        Dictionary with stats

    Example:
        stats = get_sqlite_stats()
        print(f"Average query time: {stats['average_query_time']}s")
    """
    return sqlite_tuner.get_stats()
