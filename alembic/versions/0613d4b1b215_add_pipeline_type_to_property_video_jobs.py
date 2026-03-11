"""add pipeline_type to property_video_jobs

Revision ID: 0613d4b1b215
Revises: 5bc95d55cfa1
Create Date: 2026-03-11 17:56:55.257184

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0613d4b1b215'
down_revision: Union[str, None] = '5bc95d55cfa1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('property_video_jobs', sa.Column('pipeline_type', sa.String(length=20), nullable=True))
    op.alter_column('property_video_jobs', 'property_id',
               existing_type=sa.INTEGER(),
               nullable=True)


def downgrade() -> None:
    op.alter_column('property_video_jobs', 'property_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.drop_column('property_video_jobs', 'pipeline_type')
