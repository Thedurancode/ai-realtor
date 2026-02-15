"""add_market_watchlists_table

Revision ID: b6f019cb8163
Revises: a4b8c2d1e3f6
Create Date: 2026-02-15 09:31:34.607544

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b6f019cb8163'
down_revision: Union[str, None] = 'a4b8c2d1e3f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'market_watchlists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('criteria', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=True),
        sa.Column('match_count', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('last_matched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_market_watchlists_id'), 'market_watchlists', ['id'], unique=False)
    op.create_index(op.f('ix_market_watchlists_agent_id'), 'market_watchlists', ['agent_id'], unique=False)
    op.create_index(op.f('ix_market_watchlists_is_active'), 'market_watchlists', ['is_active'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_market_watchlists_is_active'), table_name='market_watchlists')
    op.drop_index(op.f('ix_market_watchlists_agent_id'), table_name='market_watchlists')
    op.drop_index(op.f('ix_market_watchlists_id'), table_name='market_watchlists')
    op.drop_table('market_watchlists')
