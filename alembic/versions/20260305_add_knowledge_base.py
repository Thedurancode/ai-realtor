"""Add knowledge base tables for RAG

Revision ID: 20260305_kb
Revises:
Create Date: 2026-03-05
"""
from alembic import op
import sqlalchemy as sa

revision = '20260305_kb'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        'knowledge_documents',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('source', sa.String(1000)),
        sa.Column('doc_type', sa.String(50), default='plain_text'),
        sa.Column('content', sa.Text()),
        sa.Column('metadata_json', sa.Text()),
        sa.Column('chunk_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'knowledge_chunks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('document_id', sa.Integer(), sa.ForeignKey('knowledge_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('token_count', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Add vector column (pgvector)
    op.execute("ALTER TABLE knowledge_chunks ADD COLUMN embedding vector(1536)")

    # Index for fast similarity search
    op.execute("CREATE INDEX ix_knowledge_chunks_embedding ON knowledge_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)")
    op.create_index('ix_knowledge_chunks_document_id', 'knowledge_chunks', ['document_id'])


def downgrade():
    op.drop_table('knowledge_chunks')
    op.drop_table('knowledge_documents')
