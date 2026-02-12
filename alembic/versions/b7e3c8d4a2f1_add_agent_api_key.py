"""add_agent_api_key

Revision ID: b7e3c8d4a2f1
Revises: a3b7c9d2e5f1
Create Date: 2026-02-11 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7e3c8d4a2f1'
down_revision: Union[str, None] = 'a3b7c9d2e5f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('agents', sa.Column('api_key_hash', sa.String(64), nullable=True))
    op.create_index('ix_agents_api_key_hash', 'agents', ['api_key_hash'])


def downgrade() -> None:
    op.drop_index('ix_agents_api_key_hash', table_name='agents')
    op.drop_column('agents', 'api_key_hash')
