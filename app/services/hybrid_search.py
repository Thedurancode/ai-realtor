"""Hybrid Search Engine — SQLite FTS5 + Vector Cosine Similarity.

Combines full-text search with semantic vector search for optimal results.
No external vector database required — runs entirely in SQLite.
"""

import logging
import sqlite3
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_, func

from app.models.property import Property
from app.models.contact import Contact

logger = logging.getLogger(__name__)


class HybridSearchEngine:
    """SQLite FTS5 + Vector Cosine Similarity without external dependencies."""

    def __init__(self, db_path: str = None):
        """Initialize hybrid search engine.

        Args:
            db_path: Path to SQLite database (defaults to DATABASE_URL or in-memory)
        """
        if db_path is None:
            from app.config import settings
            # Extract path from DATABASE_URL if it's SQLite, otherwise use in-memory
            db_url = getattr(settings, 'DATABASE_URL', 'sqlite:///local.db')
            if db_url.startswith("sqlite:///"):
                db_path = db_url.replace("sqlite:///", "")
            else:
                # PostgreSQL - use in-memory SQLite for FTS5
                db_path = ":memory:"

        self.db_path = db_path
        self.conn = None
        self._initialize()

    def _initialize(self):
        """Set up FTS5 and vector tables."""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._setup_fts5_tables()
            self._setup_vector_tables()
            logger.info("Hybrid search engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize hybrid search: {e}")
            # Non-fatal - continue without FTS5
            self.conn = None

    def _setup_fts5_tables(self):
        """Set up full-text search tables."""
        if not self.conn:
            return

        cursor = self.conn.cursor()

        # Properties FTS5 table
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS property_fts
            USING fts5(
                address,
                city,
                description,
                content='properties',
                content_rowid='id'
            )
        """)

        # Populate FTS5 if empty
        cursor.execute("SELECT COUNT(*) FROM property_fts")
        if cursor.fetchone()[0] == 0:
            logger.info("Populating property_fts table...")
            cursor.execute("""
                INSERT INTO property_fts(rowid, address, city, description)
                SELECT id, address, city,
                       COALESCE(description, '') || ' ' || COALESCE(title, '')
                FROM properties
            """)

        # Contacts FTS5 table
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS contact_fts
            USING fts5(
                name,
                email,
                phone,
                notes,
                content='contacts',
                content_rowid='id'
            )
        """)

        self.conn.commit()

    def _setup_vector_tables(self):
        """Set up vector embedding tables."""
        if not self.conn:
            return

        cursor = self.conn.cursor()

        # Property embeddings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS property_embeddings (
                property_id INTEGER PRIMARY KEY,
                embedding BLOB,
                dimension INTEGER DEFAULT 1536,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Contact embeddings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contact_embeddings (
                contact_id INTEGER PRIMARY KEY,
                embedding BLOB,
                dimension INTEGER DEFAULT 1536,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.commit()

    def search_properties(
        self,
        db: Session,
        query: str,
        workspace_id: Optional[int] = None,
        agent_id: Optional[int] = None,
        limit: int = 10,
        use_semantic: bool = True
    ) -> List[Dict[str, Any]]:
        """Hybrid search: FTS5 + vector similarity.

        Args:
            db: Database session
            query: Search query
            workspace_id: Filter by workspace
            agent_id: Filter by agent
            limit: Max results
            use_semantic: Whether to include vector search

        Returns:
            List of matching properties with scores
        """
        results = []

        # 1. Full-text search (always available)
        fts_results = self._fts_search_properties(query, workspace_id, agent_id, limit * 5)

        # 2. Vector similarity (if embeddings exist and enabled)
        if use_semantic and self._has_embeddings():
            # Generate query embedding (would use LLM service in production)
            query_embedding = self._get_query_embedding(query)

            # Get vector similarity scores
            vector_results = self._vector_search_properties(
                query_embedding, workspace_id, agent_id, limit * 5
            )

            # 3. Combine scores (30% FTS5, 70% vector)
            combined = self._combine_scores(fts_results, vector_results)
            results = combined[:limit]
        else:
            # FTS5 only
            results = fts_results[:limit]

        # 4. Fetch full property objects
        property_ids = [r["property_id"] for r in results]
        properties = db.query(Property).filter(Property.id.in_(property_ids)).all()

        # 5. Build response with scores
        prop_map = {p.id: p for p in properties}
        final_results = []
        for r in results:
            if r["property_id"] in prop_map:
                prop = prop_map[r["property_id"]]
                final_results.append({
                    "property": prop,
                    "fts_score": r.get("fts_score", 0),
                    "vector_score": r.get("vector_score", 0),
                    "combined_score": r.get("combined_score", r.get("fts_score", 0))
                })

        return final_results

    def _fts_search_properties(
        self,
        query: str,
        workspace_id: Optional[int],
        agent_id: Optional[int],
        limit: int
    ) -> List[Dict]:
        """Full-text search using SQLite FTS5."""
        if not self.conn:
            return []

        cursor = self.conn.cursor()

        # Build FTS5 query
        # Escape special characters
        query_escaped = query.replace('"', '""')

        # Build SQL with filters
        sql = """
            SELECT rowid, bm25(property_fts) AS score
            FROM property_fts
            WHERE property_fts MATCH ?
        """
        params = [query_escaped]

        # Add workspace/agent filters via subquery
        if workspace_id is not None or agent_id is not None:
            sql += " AND rowid IN (SELECT id FROM properties WHERE 1=1"
            if workspace_id is not None:
                sql += " AND workspace_id = ?"
                params.append(workspace_id)
            if agent_id is not None:
                sql += " AND agent_id = ?"
                params.append(agent_id)
            sql += ")"

        sql += f" LIMIT {limit}"

        try:
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            return [
                {"property_id": row[0], "fts_score": -row[1]}  # BM25 lower is better, negate
                for row in rows
            ]
        except Exception as e:
            logger.warning(f"FTS5 search failed: {e}")
            return []

    def _vector_search_properties(
        self,
        query_embedding: List[float],
        workspace_id: Optional[int],
        agent_id: Optional[int],
        limit: int
    ) -> List[Dict]:
        """Vector similarity search using cosine similarity."""
        if not self.conn:
            return []

        cursor = self.conn.cursor()

        # Get all embeddings (with filters)
        sql = "SELECT property_id, embedding FROM property_embeddings WHERE 1=1"
        params = []

        if workspace_id is not None:
            sql += " AND property_id IN (SELECT id FROM properties WHERE workspace_id = ?)"
            params.append(workspace_id)
        if agent_id is not None:
            sql += " AND property_id IN (SELECT id FROM properties WHERE agent_id = ?)"
            params.append(agent_id)

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        # Calculate cosine similarities
        similarities = []
        query_norm = np.linalg.norm(query_embedding)

        for prop_id, embedding_blob in rows:
            # Deserialize embedding
            embedding = np.frombuffer(embedding_blob, dtype=np.float32)

            # Cosine similarity
            emb_norm = np.linalg.norm(embedding)
            if emb_norm > 0 and query_norm > 0:
                similarity = np.dot(embedding, query_embedding) / (emb_norm * query_norm)
            else:
                similarity = 0

            similarities.append({
                "property_id": prop_id,
                "vector_score": float(similarity)
            })

        # Sort by similarity
        similarities.sort(key=lambda x: x["vector_score"], reverse=True)

        return similarities[:limit]

    def _combine_scores(
        self,
        fts_results: List[Dict],
        vector_results: List[Dict]
    ) -> List[Dict]:
        """Combine FTS5 and vector scores."""
        # Create lookup
        fts_map = {r["property_id"]: r["fts_score"] for r in fts_results}
        vec_map = {r["property_id"]: r["vector_score"] for r in vector_results}

        # Get all unique property IDs
        all_ids = set(fts_map.keys()) | set(vec_map.keys())

        # Combine scores (30% FTS5, 70% vector)
        combined = []
        for prop_id in all_ids:
            fts_score = fts_map.get(prop_id, 0)
            vec_score = vec_map.get(prop_id, 0)

            # Normalize scores to 0-1
            fts_norm = min(fts_score / 20.0, 1.0)  # BM25 typically 0-20
            vec_norm = max(vec_score, 0)  # Cosine similarity -1 to 1

            combined_score = fts_norm * 0.3 + vec_norm * 0.7

            combined.append({
                "property_id": prop_id,
                "fts_score": fts_score,
                "vector_score": vec_score,
                "combined_score": combined_score
            })

        # Sort by combined score
        combined.sort(key=lambda x: x["combined_score"], reverse=True)

        return combined

    def _get_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for search query.

        In production, this would call an LLM embedding service.
        For now, returns a dummy embedding.
        """
        # TODO: Integrate with LLM service for real embeddings
        # from app.services.llm_service import llm_service
        # return await llm_service.embed_text(query)

        # Dummy embedding (would be 1536 dimensions for OpenAI)
        # Using smaller size for demo
        return np.random.randn(1536).tolist()

    def index_property(self, property_id: int, text: str, embedding: Optional[List[float]] = None):
        """Index a property for FTS5 and vector search.

        Args:
            property_id: Property ID
            text: Text content to index (address, description, etc.)
            embedding: Vector embedding (optional)
        """
        if not self.conn:
            return

        cursor = self.conn.cursor()

        try:
            # Update FTS5
            cursor.execute("""
                INSERT OR REPLACE INTO property_fts(rowid, address, city, description)
                VALUES (?, '', '', ?)
            """, (property_id, text))

            # Update vector embedding
            if embedding:
                embedding_bytes = np.array(embedding, dtype=np.float32).tobytes()
                cursor.execute("""
                    INSERT OR REPLACE INTO property_embeddings(property_id, embedding, dimension, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (property_id, embedding_bytes, len(embedding)))

            self.conn.commit()

        except Exception as e:
            logger.error(f"Failed to index property {property_id}: {e}")
            self.conn.rollback()

    def _has_embeddings(self) -> bool:
        """Check if any embeddings exist."""
        if not self.conn:
            return False

        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM property_embeddings")
        count = cursor.fetchone()[0]
        return count > 0

    def search_similar_properties(
        self,
        db: Session,
        property_id: int,
        limit: int = 10
    ) -> List[Property]:
        """Find properties similar to a given property using vector search.

        Args:
            db: Database session
            property_id: Reference property ID
            limit: Max results

        Returns:
            List of similar properties
        """
        if not self.conn:
            # Fallback to database query without vectors
            prop = db.query(Property).filter(Property.id == property_id).first()
            if not prop:
                return []

            # Simple similarity by city and property type
            similar = db.query(Property).filter(
                Property.id != property_id,
                Property.city == prop.city,
                Property.property_type == prop.property_type
            ).limit(limit).all()

            return similar

        cursor = self.conn.cursor()

        # Get reference property embedding
        cursor.execute(
            "SELECT embedding FROM property_embeddings WHERE property_id = ?",
            (property_id,)
        )
        row = cursor.fetchone()

        if not row:
            # No embedding found, fallback to DB query
            return self.search_similar_properties(db, property_id, limit)

        ref_embedding = np.frombuffer(row[0], dtype=np.float32)

        # Get all other embeddings
        cursor.execute(
            "SELECT property_id, embedding FROM property_embeddings WHERE property_id != ?",
            (property_id,)
        )
        rows = cursor.fetchall()

        # Calculate similarities
        similarities = []
        ref_norm = np.linalg.norm(ref_embedding)

        for prop_id, embedding_blob in rows:
            embedding = np.frombuffer(embedding_blob, dtype=np.float32)
            emb_norm = np.linalg.norm(embedding)

            if emb_norm > 0 and ref_norm > 0:
                similarity = np.dot(embedding, ref_embedding) / (emb_norm * ref_norm)
                similarities.append((prop_id, float(similarity)))

        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Fetch top properties
        top_ids = [pid for pid, _ in similarities[:limit]]
        properties = db.query(Property).filter(Property.id.in_(top_ids)).all()

        # Sort by similarity order
        prop_map = {p.id: p for p in properties}
        sorted_properties = []
        for pid, _ in similarities[:limit]:
            if pid in prop_map:
                sorted_properties.append(prop_map[pid])

        return sorted_properties

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()


# Global instance
hybrid_search = HybridSearchEngine()
