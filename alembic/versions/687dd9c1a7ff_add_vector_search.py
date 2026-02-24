"""add_vector_search

Revision ID: 687dd9c1a7ff
Revises: 0f30c29729ce
Create Date: 2026-02-07 18:10:25.064245

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '687dd9c1a7ff'
down_revision: Union[str, None] = '0f30c29729ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    import logging
    # Check if we're using SQLite
    conn = op.get_bind()
    dialect_name = conn.dialect.name

    if dialect_name == 'sqlite':
        logging.warning(
            "SQLite detected — skipping pgvector extension and vector columns. "
            "Vector search requires PostgreSQL with pgvector extension."
        )
        return

    # Check if pgvector extension is available without breaking the transaction
    try:
        result = conn.execute(sa.text(
            "SELECT 1 FROM pg_available_extensions WHERE name = 'vector'"
        ))
        if not result.fetchone():
            logging.warning(
                "pgvector extension not available — skipping vector search columns. "
                "Install pgvector on the database and re-run this migration to enable."
            )
            return

        conn.execute(sa.text('CREATE EXTENSION IF NOT EXISTS vector'))

        # Add embedding columns directly as vector type
        op.execute('ALTER TABLE properties ADD COLUMN IF NOT EXISTS embedding vector(1536)')
        op.execute('ALTER TABLE property_recaps ADD COLUMN IF NOT EXISTS embedding vector(1536)')
        op.execute('ALTER TABLE dossiers ADD COLUMN IF NOT EXISTS embedding vector(1536)')
        op.execute('ALTER TABLE evidence ADD COLUMN IF NOT EXISTS embedding vector(1536)')

        # Create HNSW indexes for fast similarity search
        op.execute('CREATE INDEX IF NOT EXISTS idx_properties_embedding ON properties USING hnsw (embedding vector_cosine_ops)')
        op.execute('CREATE INDEX IF NOT EXISTS idx_recaps_embedding ON property_recaps USING hnsw (embedding vector_cosine_ops)')
        op.execute('CREATE INDEX IF NOT EXISTS idx_dossiers_embedding ON dossiers USING hnsw (embedding vector_cosine_ops)')
        op.execute('CREATE INDEX IF NOT EXISTS idx_evidence_embedding ON evidence USING hnsw (embedding vector_cosine_ops)')
    except Exception as e:
        logging.warning(f"Failed to add vector search: {e}")


def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS idx_evidence_embedding')
    op.execute('DROP INDEX IF EXISTS idx_dossiers_embedding')
    op.execute('DROP INDEX IF EXISTS idx_recaps_embedding')
    op.execute('DROP INDEX IF EXISTS idx_properties_embedding')

    op.execute('ALTER TABLE evidence DROP COLUMN IF EXISTS embedding')
    op.execute('ALTER TABLE dossiers DROP COLUMN IF EXISTS embedding')
    op.execute('ALTER TABLE property_recaps DROP COLUMN IF EXISTS embedding')
    op.execute('ALTER TABLE properties DROP COLUMN IF EXISTS embedding')

    op.execute('DROP EXTENSION IF EXISTS vector')
