"""Add timeline projects table

Revision ID: 20250225_add_timeline_projects
Revises: 20250225_add_remotion_render_jobs
Create Date: 2026-02-25

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250225_add_timeline_projects'
down_revision = '20250225_add_remotion_render_jobs'
branch_labels = None
depends_on = None


def upgrade():
    # Create timeline_projects table
    op.create_table(
        'timeline_projects',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('timeline_data', sa.JSON(), nullable=False),
        sa.Column('fps', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('width', sa.Integer(), nullable=False, server_default='1080'),
        sa.Column('height', sa.Integer(), nullable=False, server_default='1920'),
        sa.Column('status', sa.String(), nullable=False, server_default='draft'),
        sa.Column('render_job_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('rendered_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id']),
        sa.ForeignKeyConstraint(['render_job_id'], ['render_jobs.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_timeline_projects_id', 'timeline_projects', ['id'])
    op.create_index('ix_timeline_projects_agent_id', 'timeline_projects', ['agent_id'])
    op.create_index('ix_timeline_projects_status', 'timeline_projects', ['status'])
    op.create_index('ix_timeline_projects_render_job_id', 'timeline_projects', ['render_job_id'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_timeline_projects_render_job_id', table_name='timeline_projects')
    op.drop_index('ix_timeline_projects_status', table_name='timeline_projects')
    op.drop_index('ix_timeline_projects_agent_id', table_name='timeline_projects')
    op.drop_index('ix_timeline_projects_id', table_name='timeline_projects')

    # Drop table
    op.drop_table('timeline_projects')
