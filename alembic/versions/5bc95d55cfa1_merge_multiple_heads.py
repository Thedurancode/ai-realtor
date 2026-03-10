"""merge multiple heads

Revision ID: 5bc95d55cfa1
Revises: 1ed987f5fee3, 20260309_add_tc, 26c83897e593
Create Date: 2026-03-10 14:16:16.673111

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5bc95d55cfa1'
down_revision: Union[str, None] = ('1ed987f5fee3', '20260309_add_tc', '26c83897e593')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
