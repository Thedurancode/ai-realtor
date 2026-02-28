"""add workspace_id to agents

Revision ID: add_workspace_id_to_agents
Revises:
Create Date: 2026-02-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_workspace_id_to_agents'
down_revision = None  # Standalone migration
branch_labels = None
depends_on = None


def upgrade():
    # Add workspace_id column to agents table
    op.add_column('agents', sa.Column('workspace_id', sa.Integer(), nullable=True))
    # Create index for workspace_id
    op.create_index('ix_agents_workspace_id', 'agents', ['workspace_id'])

    # Note: We're not creating a foreign key constraint to avoid dependency on workspaces table
    # The workspace_id can be NULL for existing agents


def downgrade():
    # Remove index
    op.drop_index('ix_agents_workspace_id', 'agents')
    # Remove column
    op.drop_column('agents', 'workspace_id')
