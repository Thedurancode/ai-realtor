"""Add PVC voices table for Professional Voice Clones (PVC)

Revision ID: add_pvc_voices_table
Revises: add_pvc_voices_table

"""
from alembic import op
from alembic import revision, Revision
from sqlalchemy import inspect_table
from sqlalchemy.dialects import postgresql


def upgrade():
    op.add_table(
        'pvc_voices',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('language', sa.String(10), default='en'),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('status', sa.String(20), default='creating'),
        sa.Column('created_at', sa.DateTime(timezone=True), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), default=sa.func.now()),
        sa.Column('sample_count', sa.Integer, default=0),
        sa.Column('speakers_count', sa.Integer, default=0),
        sa.Column('model_id', sa.String(100), nullable=True),
        sa.Column('training_progress', sa.String(100), nullable=True),
        sa.Column('is_trained', sa.Boolean, default=False),
        sa.Column('trained_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Column('agent_id', sa.Integer, sa.ForeignKey('agents.id'), nullable=True),
        sa.Column('property_id', sa.Integer, sa.ForeignKey('properties.id'), nullable=True),
    )

    op.execute("DROP TABLE IF EXISTS pvc_voices CASCADE")
    op.execute("""
        CREATE TABLE pvc_voices (
            id VARCHAR(100) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            language VARCHAR(10) NOT NULL DEFAULT 'en',
            description TEXT,
            status VARCHAR(20) NOT NULL DEFAULT 'creating',
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            sample_count INTEGER DEFAULT 0,
            speakers_count INTEGER DEFAULT 0,
            model_id VARCHAR(100),
            training_progress TEXT,
            is_trained BOOLEAN DEFAULT FALSE,
            trained_at TIMESTAMP WITHOUT TIME ZONE,
            metadata JSONB,
            agent_id INTEGER REFERENCES agents(id),
            property_id INTEGER REFERENCES properties(id)
        )
    """)


def downgrade():
    op.drop_table('pvc_voices')
