"""
Create Customer Portal Tables

Revision ID: 002_create_portal
Create Date: 2026-02-26
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '002_create_portal'
down_revision = '001_create_activity_events'
branch_labels = None
depends_on = None


def upgrade():
    # Create portal_users table
    op.create_table(
        'portal_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('company', sa.String(), nullable=True),
        sa.Column('role', sa.String(), nullable=False, server_default='client'),
        sa.Column('client_type', sa.String(), nullable=True),
        sa.Column('invited_by_agent_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('verification_token', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('notification_email', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notification_sms', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('notification_push', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['invited_by_agent_id'], ['agents.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_portal_users_id', 'portal_users', ['id'])
    op.create_index('ix_portal_users_email', 'portal_users', ['email'])

    # Create property_access table
    op.create_table(
        'property_access',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('portal_user_id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('access_level', sa.String(), nullable=False, server_default='view'),
        sa.Column('relationship', sa.String(), nullable=True),
        sa.Column('can_view_details', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('can_view_contracts', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('can_view_documents', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('can_sign_contracts', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_view_price', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('invited_at', sa.DateTime(), nullable=False),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['portal_user_id'], ['portal_users.id']),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_property_access_id', 'property_access', ['id'])

    # Create portal_activity table
    op.create_table(
        'portal_activity',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('portal_user_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=True),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['portal_user_id'], ['portal_users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_portal_activity_id', 'portal_activity', ['id'])
    op.create_index('ix_portal_activity_created_at', 'portal_activity', ['created_at'])


def downgrade():
    op.drop_table('portal_activity')
    op.drop_table('property_access')
    op.drop_table('portal_users')
