"""merge_all_heads_with_kb

Revision ID: 26c83897e593
Revises: 20260305_kb, e58e55272f67
Create Date: 2026-03-05 23:20:40.028465

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '26c83897e593'
down_revision: Union[str, None] = ('20260305_kb', 'e58e55272f67')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
