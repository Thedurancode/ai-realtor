"""
Embedding Service

Generates OpenAI text-embedding-3-small vectors (1536 dims) and performs
pgvector similarity searches across properties, recaps, dossiers, and evidence.
"""
import logging
import time
from typing import Optional

from openai import OpenAI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.models.property import Property
from app.models.property_recap import PropertyRecap
from app.models.dossier import Dossier
from app.models.evidence_item import EvidenceItem

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMS = 1536


class EmbeddingService:
    def __init__(self):
        self._client = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            api_key = settings.openai_api_key
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set")
            self._client = OpenAI(api_key=api_key)
        return self._client

    # ── Core embedding ──────────────────────────────────────────────

    def generate_embedding(self, text_input: str) -> list[float]:
        """Generate a 1536-dim embedding for a single text."""
        if not text_input or not text_input.strip():
            raise ValueError("Cannot embed empty text")
        # Truncate to ~8000 tokens (~32K chars) to stay within model limits
        truncated = text_input[:32000]
        resp = self.client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=truncated,
        )
        return resp.data[0].embedding

    def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for up to 2048 texts in one API call."""
        if not texts:
            return []
        truncated = [t[:32000] for t in texts if t and t.strip()]
        resp = self.client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=truncated,
        )
        return [d.embedding for d in resp.data]

    # ── Embed individual records ────────────────────────────────────

    def _property_text(self, prop: Property) -> str:
        """Build searchable text from property fields."""
        parts = [
            prop.address or "",
            prop.city or "",
            prop.state or "",
            prop.zip_code or "",
        ]
        if prop.property_type:
            parts.append(prop.property_type.value)
        if prop.status:
            parts.append(f"status: {prop.status.value}")
        if prop.price:
            parts.append(f"price: ${prop.price:,.0f}")
        if prop.bedrooms:
            parts.append(f"{prop.bedrooms} bedrooms")
        if prop.bathrooms:
            parts.append(f"{prop.bathrooms} bathrooms")
        if prop.square_feet:
            parts.append(f"{prop.square_feet} sqft")
        if prop.year_built:
            parts.append(f"built {prop.year_built}")
        if prop.description:
            parts.append(prop.description)
        if prop.title:
            parts.append(prop.title)
        return " | ".join(p for p in parts if p)

    def embed_property(self, db: Session, property_id: int) -> bool:
        """Embed a property and store the vector."""
        prop = db.query(Property).get(property_id)
        if not prop:
            return False
        txt = self._property_text(prop)
        if not txt.strip():
            return False
        vec = self.generate_embedding(txt)
        db.execute(
            text("UPDATE properties SET embedding = :vec WHERE id = :pid"),
            {"vec": str(vec), "pid": property_id},
        )
        db.commit()
        return True

    def embed_recap(self, db: Session, recap_id: int) -> bool:
        """Embed a property recap's text."""
        recap = db.query(PropertyRecap).get(recap_id)
        if not recap or not recap.recap_text:
            return False
        vec = self.generate_embedding(recap.recap_text)
        db.execute(
            text("UPDATE property_recaps SET embedding = :vec WHERE id = :rid"),
            {"vec": str(vec), "rid": recap_id},
        )
        db.commit()
        return True

    def embed_dossier(self, db: Session, dossier_id: int) -> bool:
        """Embed a research dossier's markdown."""
        dossier = db.query(Dossier).get(dossier_id)
        if not dossier or not dossier.markdown:
            return False
        vec = self.generate_embedding(dossier.markdown)
        db.execute(
            text("UPDATE dossiers SET embedding = :vec WHERE id = :did"),
            {"vec": str(vec), "did": dossier_id},
        )
        db.commit()
        return True

    def embed_evidence(self, db: Session, evidence_id: int) -> bool:
        """Embed an evidence item's claim + excerpt."""
        ev = db.query(EvidenceItem).get(evidence_id)
        if not ev or not ev.claim:
            return False
        txt = ev.claim
        if ev.raw_excerpt:
            txt += " | " + ev.raw_excerpt
        vec = self.generate_embedding(txt)
        db.execute(
            text("UPDATE evidence SET embedding = :vec WHERE id = :eid"),
            {"vec": str(vec), "eid": evidence_id},
        )
        db.commit()
        return True

    # ── Semantic search ─────────────────────────────────────────────

    def search_properties(
        self,
        db: Session,
        query: str,
        limit: int = 10,
        status: Optional[str] = None,
        property_type: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
    ) -> list[dict]:
        """Semantic search across properties using cosine similarity."""
        query_vec = self.generate_embedding(query)

        # Build dynamic WHERE clause for hybrid filtering
        conditions = ["p.embedding IS NOT NULL"]
        params: dict = {"qvec": str(query_vec), "lim": limit}

        if status:
            conditions.append("p.status = :status")
            params["status"] = status
        if property_type:
            conditions.append("p.property_type = :ptype")
            params["ptype"] = property_type
        if min_price is not None:
            conditions.append("p.price >= :min_price")
            params["min_price"] = min_price
        if max_price is not None:
            conditions.append("p.price <= :max_price")
            params["max_price"] = max_price

        where_clause = " AND ".join(conditions)

        sql = text(f"""
            SELECT p.id, p.title, p.address, p.city, p.state, p.zip_code,
                   p.price, p.bedrooms, p.bathrooms, p.square_feet,
                   p.property_type, p.status,
                   1 - (p.embedding <=> :qvec::vector) AS similarity
            FROM properties p
            WHERE {where_clause}
            ORDER BY p.embedding <=> :qvec::vector
            LIMIT :lim
        """)

        rows = db.execute(sql, params).fetchall()
        return [
            {
                "id": r.id,
                "title": r.title,
                "address": f"{r.address}, {r.city}, {r.state} {r.zip_code}",
                "price": r.price,
                "bedrooms": r.bedrooms,
                "bathrooms": r.bathrooms,
                "square_feet": r.square_feet,
                "property_type": r.property_type,
                "status": r.status,
                "similarity": round(float(r.similarity), 4),
            }
            for r in rows
        ]

    def search_research(
        self,
        db: Session,
        query: str,
        dossier_limit: int = 5,
        evidence_limit: int = 10,
    ) -> dict:
        """Search across dossiers and evidence items."""
        query_vec = self.generate_embedding(query)
        vec_str = str(query_vec)

        # Search dossiers
        dossier_sql = text("""
            SELECT d.id, d.research_property_id, d.job_id,
                   LEFT(d.markdown, 300) AS snippet,
                   1 - (d.embedding <=> :qvec::vector) AS similarity
            FROM dossiers d
            WHERE d.embedding IS NOT NULL
            ORDER BY d.embedding <=> :qvec::vector
            LIMIT :lim
        """)
        dossier_rows = db.execute(dossier_sql, {"qvec": vec_str, "lim": dossier_limit}).fetchall()

        # Search evidence
        evidence_sql = text("""
            SELECT e.id, e.research_property_id, e.category, e.claim,
                   e.source_url, e.confidence,
                   LEFT(e.raw_excerpt, 200) AS snippet,
                   1 - (e.embedding <=> :qvec::vector) AS similarity
            FROM evidence e
            WHERE e.embedding IS NOT NULL
            ORDER BY e.embedding <=> :qvec::vector
            LIMIT :lim
        """)
        evidence_rows = db.execute(evidence_sql, {"qvec": vec_str, "lim": evidence_limit}).fetchall()

        return {
            "dossiers": [
                {
                    "id": r.id,
                    "research_property_id": r.research_property_id,
                    "job_id": r.job_id,
                    "snippet": r.snippet,
                    "similarity": round(float(r.similarity), 4),
                }
                for r in dossier_rows
            ],
            "evidence": [
                {
                    "id": r.id,
                    "research_property_id": r.research_property_id,
                    "category": r.category,
                    "claim": r.claim,
                    "source_url": r.source_url,
                    "confidence": r.confidence,
                    "snippet": r.snippet,
                    "similarity": round(float(r.similarity), 4),
                }
                for r in evidence_rows
            ],
        }

    def find_similar_properties(
        self,
        db: Session,
        property_id: int,
        limit: int = 5,
    ) -> list[dict]:
        """Find properties similar to a given property using recap or property embedding."""
        # Try recap embedding first (richer data), fall back to property embedding
        sql = text("""
            WITH source_vec AS (
                SELECT COALESCE(
                    (SELECT pr.embedding FROM property_recaps pr WHERE pr.property_id = :pid AND pr.embedding IS NOT NULL),
                    (SELECT p2.embedding FROM properties p2 WHERE p2.id = :pid AND p2.embedding IS NOT NULL)
                ) AS vec
            )
            SELECT p.id, p.title, p.address, p.city, p.state, p.zip_code,
                   p.price, p.bedrooms, p.bathrooms, p.square_feet,
                   p.property_type, p.status,
                   1 - (p.embedding <=> sv.vec) AS similarity
            FROM properties p, source_vec sv
            WHERE p.id != :pid
              AND p.embedding IS NOT NULL
              AND sv.vec IS NOT NULL
            ORDER BY p.embedding <=> sv.vec
            LIMIT :lim
        """)
        rows = db.execute(sql, {"pid": property_id, "lim": limit}).fetchall()
        return [
            {
                "id": r.id,
                "title": r.title,
                "address": f"{r.address}, {r.city}, {r.state} {r.zip_code}",
                "price": r.price,
                "bedrooms": r.bedrooms,
                "bathrooms": r.bathrooms,
                "square_feet": r.square_feet,
                "property_type": r.property_type,
                "status": r.status,
                "similarity": round(float(r.similarity), 4),
            }
            for r in rows
        ]

    # ── Backfill ────────────────────────────────────────────────────

    def backfill(self, db: Session, table: str = "all") -> dict:
        """Backfill embeddings for existing records missing them."""
        start = time.time()
        results = {}

        tables_to_process = []
        if table in ("all", "properties"):
            tables_to_process.append("properties")
        if table in ("all", "property_recaps"):
            tables_to_process.append("property_recaps")
        if table in ("all", "dossiers"):
            tables_to_process.append("dossiers")
        if table in ("all", "evidence"):
            tables_to_process.append("evidence")

        for tbl in tables_to_process:
            embedded = 0
            skipped = 0
            errors = 0

            if tbl == "properties":
                rows = db.execute(text("SELECT id FROM properties WHERE embedding IS NULL")).fetchall()
                for row in rows:
                    try:
                        if self.embed_property(db, row.id):
                            embedded += 1
                        else:
                            skipped += 1
                    except Exception as e:
                        logger.warning(f"Error embedding property {row.id}: {e}")
                        errors += 1

            elif tbl == "property_recaps":
                rows = db.execute(text("SELECT id FROM property_recaps WHERE embedding IS NULL")).fetchall()
                for row in rows:
                    try:
                        if self.embed_recap(db, row.id):
                            embedded += 1
                        else:
                            skipped += 1
                    except Exception as e:
                        logger.warning(f"Error embedding recap {row.id}: {e}")
                        errors += 1

            elif tbl == "dossiers":
                rows = db.execute(text("SELECT id FROM dossiers WHERE embedding IS NULL")).fetchall()
                for row in rows:
                    try:
                        if self.embed_dossier(db, row.id):
                            embedded += 1
                        else:
                            skipped += 1
                    except Exception as e:
                        logger.warning(f"Error embedding dossier {row.id}: {e}")
                        errors += 1

            elif tbl == "evidence":
                rows = db.execute(text("SELECT id FROM evidence WHERE embedding IS NULL")).fetchall()
                for row in rows:
                    try:
                        if self.embed_evidence(db, row.id):
                            embedded += 1
                        else:
                            skipped += 1
                    except Exception as e:
                        logger.warning(f"Error embedding evidence {row.id}: {e}")
                        errors += 1

            results[tbl] = {
                "total": embedded + skipped + errors,
                "embedded": embedded,
                "skipped": skipped,
                "errors": errors,
            }

        duration = round(time.time() - start, 2)
        return {"tables": results, "duration_seconds": duration}


# Singleton
embedding_service = EmbeddingService()
