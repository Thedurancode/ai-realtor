"""Add Remotion render jobs table

Revision ID: 20250225_add_remotion_render_jobs
Revises: 20250224_voice_assistant_tables
Create Date: 2026-02-25

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '20250225_add_remotion_render_jobs'
down_revision = '20250224_voice_assistant_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Create render_jobs table
    op.create_table(
        'render_jobs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.String(), nullable=False),
        sa.Column('composition_id', sa.String(), nullable=False),
        sa.Column('input_props', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='queued'),
        sa.Column('progress', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('output_url', sa.Text(), nullable=True),
        sa.Column('output_bucket', sa.String(), nullable=True),
        sa.Column('output_key', sa.String(), nullable=True),
        sa.Column('webhook_url', sa.Text(), nullable=True),
        sa.Column('webhook_sent', sa.String(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', sa.JSON(), nullable=True),
        sa.Column('current_frame', sa.Integer(), nullable=True),
        sa.Column('total_frames', sa.Integer(), nullable=True),
        sa.Column('eta_seconds', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_render_jobs_id', 'render_jobs', ['id'])
    op.create_index('ix_render_jobs_template_id', 'render_jobs', ['template_id'])
    op.create_index('ix_render_jobs_status', 'render_jobs', ['status'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_render_jobs_status', table_name='render_jobs')
    op.drop_index('ix_render_jobs_template_id', table_name='render_jobs')
    op.drop_index('ix_render_jobs_id', table_name='render_jobs')

    # Drop table
    op.drop_table('render_jobs')
