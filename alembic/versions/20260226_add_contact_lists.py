"""add contact lists

Revision ID: 20260226_add_contact_lists
Revises: 20260226_add_direct_mail
Create Date: 2026-02-26 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260226_add_contact_lists'
down_revision = '20260226_add_direct_mail'
branch_labels = None
depends_on = None


def upgrade():
    # Create contact_lists table
    op.create_table(
        'contact_lists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('list_type', postgresql.ENUM(name='list_type', create_type=True), nullable=False),
        sa.Column('smart_rule', postgresql.ENUM(name='smart_rule', create_type=True), nullable=True),
        sa.Column('filters', sa.JSON(), nullable=True),
        sa.Column('contact_ids', sa.JSON(), nullable=True),
        sa.Column('campaign_id', sa.Integer(), nullable=True),
        sa.Column('auto_refresh', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_refreshed_at', sa.DateTime(), nullable=True),
        sa.Column('refresh_interval_hours', sa.Integer(), nullable=False, server_default='24'),
        sa.Column('total_contacts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_contact_added_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.ForeignKeyConstraint(['campaign_id'], ['direct_mail_campaigns.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contact_lists_agent_id'), 'contact_lists', ['agent_id'], unique=False)
    op.create_index(op.f('ix_contact_lists_name'), 'contact_lists', ['name'], unique=False)

    # Add contact_lists relationship to agents (would need to update Agent model)
    # This is done in the model file, not migration


def downgrade():
    op.drop_index(op.f('ix_contact_lists_name'), table_name='contact_lists')
    op.drop_index(op.f('ix_contact_lists_agent_id'), table_name='contact_lists')
    op.drop_table('contact_lists')

    # Drop ENUM types
    op.execute('DROP TYPE IF EXISTS list_type')
    op.execute('DROP TYPE IF EXISTS smart_rule')
