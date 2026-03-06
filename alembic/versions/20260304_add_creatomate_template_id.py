"""Add creatomate_template_id to agent_brands

Revision ID: a3c9f1e28d47
Revises: 72444e81856b
Create Date: 2026-03-04
"""
from alembic import op
import sqlalchemy as sa

revision = 'a3c9f1e28d47'
down_revision = '72444e81856b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('agent_brands', sa.Column('creatomate_template_id', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('agent_brands', 'creatomate_template_id')
