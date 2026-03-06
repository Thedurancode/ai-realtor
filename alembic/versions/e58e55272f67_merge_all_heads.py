"""merge_all_heads

Revision ID: e58e55272f67
Revises: 20250222_add_workspace_and_security, 20250225_add_timeline_projects, 004_add_calendar, 20260226_add_contact_lists, 20260227_add_enabled_to_scheduled_tasks, add_workspace_id_to_agents, make_generated_script_nullable, 20260302_add_products, b7d4e2f38a16, 83a5f2d91e7c, 005_add_videogen, d1e2f3a4b5c6, d395fd06467d
Create Date: 2026-03-05 12:38:25.514952

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e58e55272f67'
down_revision: Union[str, None] = ('20250222_add_workspace_and_security', '20250225_add_timeline_projects', '004_add_calendar', '20260226_add_contact_lists', '20260227_add_enabled_to_scheduled_tasks', 'add_workspace_id_to_agents', 'make_generated_script_nullable', '20260302_add_products', 'b7d4e2f38a16', '83a5f2d91e7c', '005_add_videogen', 'd1e2f3a4b5c6', 'd395fd06467d')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
