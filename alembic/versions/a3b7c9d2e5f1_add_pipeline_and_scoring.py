"""add_pipeline_and_scoring

Revision ID: a3b7c9d2e5f1
Revises: 687dd9c1a7ff
Create Date: 2026-02-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3b7c9d2e5f1'
down_revision: Union[str, None] = '687dd9c1a7ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('properties', sa.Column('deal_score', sa.Float(), nullable=True))
    op.add_column('properties', sa.Column('score_grade', sa.String(2), nullable=True))
    op.add_column('properties', sa.Column('score_breakdown', sa.JSON(), nullable=True))
    op.add_column('properties', sa.Column('pipeline_status', sa.String(20), nullable=True))
    op.add_column('properties', sa.Column('pipeline_started_at', sa.DateTime(), nullable=True))
    op.add_column('properties', sa.Column('pipeline_completed_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('properties', 'pipeline_completed_at')
    op.drop_column('properties', 'pipeline_started_at')
    op.drop_column('properties', 'pipeline_status')
    op.drop_column('properties', 'score_breakdown')
    op.drop_column('properties', 'score_grade')
    op.drop_column('properties', 'deal_score')
