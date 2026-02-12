"""Add conversation history table

Revision ID: c9d3f7a1b2e5
Revises: b7e3c8d4a2f1
Create Date: 2026-02-12

"""
from typing import Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9d3f7a1b2e5'
down_revision: Union[str, None] = 'b7e3c8d4a2f1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'conversation_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(128), nullable=False),
        sa.Column('tool_name', sa.String(128), nullable=False),
        sa.Column('input_summary', sa.Text(), nullable=True),
        sa.Column('output_summary', sa.Text(), nullable=True),
        sa.Column('input_data', sa.JSON(), nullable=True),
        sa.Column('output_data', sa.JSON(), nullable=True),
        sa.Column('success', sa.Integer(), default=1),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_conversation_history_id', 'conversation_history', ['id'])
    op.create_index('ix_conversation_history_session_id', 'conversation_history', ['session_id'])
    op.create_index('ix_conversation_history_tool_name', 'conversation_history', ['tool_name'])
    op.create_index('ix_conversation_history_created_at', 'conversation_history', ['created_at'])
    op.create_index('ix_conversation_history_session_created', 'conversation_history', ['session_id', 'created_at'])


def downgrade() -> None:
    op.drop_index('ix_conversation_history_session_created')
    op.drop_index('ix_conversation_history_created_at')
    op.drop_index('ix_conversation_history_tool_name')
    op.drop_index('ix_conversation_history_session_id')
    op.drop_index('ix_conversation_history_id')
    op.drop_table('conversation_history')
