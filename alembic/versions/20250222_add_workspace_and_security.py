"""Add workspaces, API keys, command permissions, and cron scheduler.

Revision ID: 20250222_add_workspace_and_security
Revises:
Create Date: 2025-02-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250222_add_workspace_and_security'
down_revision = 'c8d2e4f5a7b9'  # After property pipeline replacement
branch_labels = None
depends_on = None


def upgrade():
    # Create workspaces table
    op.create_table(
        'workspaces',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('owner_email', sa.String(length=255), nullable=False),
        sa.Column('owner_name', sa.String(length=255), nullable=True),
        sa.Column('api_key_hash', sa.String(length=255), nullable=False),
        sa.Column('settings', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('subscription_tier', sa.String(length=50), nullable=True, server_default='free'),
        sa.Column('max_agents', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('max_properties', sa.Integer(), nullable=True, server_default='50'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workspaces_id'), 'workspaces', ['id'])
    op.create_index(op.f('ix_workspaces_owner_email'), 'workspaces', ['owner_email'])
    op.create_index(op.f('ix_workspaces_is_active'), 'workspaces', ['is_active'])
    op.create_index(op.f('ix_workspaces_deleted_at'), 'workspaces', ['deleted_at'])

    # Create workspace_api_keys table
    op.create_table(
        'workspace_api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('key_hash', sa.String(length=255), nullable=False),
        sa.Column('key_prefix', sa.String(length=10), nullable=False),
        sa.Column('scopes', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workspace_api_keys_id'), 'workspace_api_keys', ['id'])
    op.create_index(op.f('ix_workspace_api_keys_workspace_id'), 'workspace_api_keys', ['workspace_id'])
    op.create_index(op.f('ix_workspace_api_keys_agent_id'), 'workspace_api_keys', ['agent_id'])
    op.create_index(op.f('ix_workspace_api_keys_key_hash'), 'workspace_api_keys', ['key_hash'], unique=True)
    op.create_index(op.f('ix_workspace_api_keys_expires_at'), 'workspace_api_keys', ['expires_at'])
    op.create_index(op.f('ix_workspace_api_keys_revoked_at'), 'workspace_api_keys', ['revoked_at'])

    # Create command_permissions table
    op.create_table(
        'command_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=True),
        sa.Column('command_pattern', sa.String(length=100), nullable=False),
        sa.Column('permission', sa.String(length=20), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_command_permissions_id'), 'command_permissions', ['id'])
    op.create_index(op.f('ix_command_permissions_workspace_id'), 'command_permissions', ['workspace_id'])
    op.create_index(op.f('ix_command_permissions_agent_id'), 'command_permissions', ['agent_id'])
    op.create_index(op.f('ix_command_permissions_command_pattern'), 'command_permissions', ['command_pattern'])

    # Add workspace_id to existing tables (for multi-tenant isolation)
    # Agents
    op.add_column('agents', sa.Column('workspace_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_agents_workspace_id', 'agents', 'workspaces', ['workspace_id'], ['id'])
    op.create_index('ix_agents_workspace_id', 'agents', ['workspace_id'])

    # Properties
    op.add_column('properties', sa.Column('workspace_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_properties_workspace_id', 'properties', 'workspaces', ['workspace_id'], ['id'])
    op.create_index('ix_properties_workspace_id', 'properties', ['workspace_id'])

    # Contacts
    op.add_column('contacts', sa.Column('workspace_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_contacts_workspace_id', 'contacts', 'workspaces', ['workspace_id'], ['id'])
    op.create_index('ix_contacts_workspace_id', 'contacts', ['workspace_id'])

    # Create hybrid search tables (FTS5 and vector embeddings)
    # Note: FTS5 tables are created at runtime by the service, not in migration

    # Property embeddings table
    op.create_table(
        'property_embeddings',
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('embedding', sa.LargeBinary(), nullable=True),
        sa.Column('dimension', sa.Integer(), nullable=True, server_default='1536'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('property_id')
    )

    # Contact embeddings table
    op.create_table(
        'contact_embeddings',
        sa.Column('contact_id', sa.Integer(), nullable=False),
        sa.Column('embedding', sa.LargeBinary(), nullable=True),
        sa.Column('dimension', sa.Integer(), nullable=True, server_default='1536'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('contact_id')
    )

    # Add cron_expression to scheduled_tasks table (if it exists)
    # Check if column exists first to avoid errors
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'scheduled_tasks' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('scheduled_tasks')]

        if 'cron_expression' not in columns:
            op.add_column('scheduled_tasks', sa.Column('cron_expression', sa.String(length=100), nullable=True))
            op.add_column('scheduled_tasks', sa.Column('handler_name', sa.String(length=100), nullable=True))
            op.add_column('scheduled_tasks', sa.Column('retry_count', sa.Integer(), nullable=True, server_default='0'))
            op.add_column('scheduled_tasks', sa.Column('max_retries', sa.Integer(), nullable=True, server_default='3'))
            op.add_column('scheduled_tasks', sa.Column('last_result', postgresql.JSONB(), nullable=True))


def downgrade():
    # Drop hybrid search tables
    op.drop_table('contact_embeddings')
    op.drop_table('property_embeddings')

    # Remove cron columns from scheduled_tasks if they were added
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'scheduled_tasks' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('scheduled_tasks')]

        if 'last_result' in columns:
            op.drop_column('scheduled_tasks', 'last_result')
        if 'max_retries' in columns:
            op.drop_column('scheduled_tasks', 'max_retries')
        if 'retry_count' in columns:
            op.drop_column('scheduled_tasks', 'retry_count')
        if 'handler_name' in columns:
            op.drop_column('scheduled_tasks', 'handler_name')
        if 'cron_expression' in columns:
            op.drop_column('scheduled_tasks', 'cron_expression')

    # Remove workspace_id from existing tables
    op.drop_index('ix_contacts_workspace_id', table_name='contacts')
    op.drop_constraint('fk_contacts_workspace_id', 'contacts', type_='foreignkey')
    op.drop_column('contacts', 'workspace_id')

    op.drop_index('ix_properties_workspace_id', table_name='properties')
    op.drop_constraint('fk_properties_workspace_id', 'properties', type_='foreignkey')
    op.drop_column('properties', 'workspace_id')

    op.drop_index('ix_agents_workspace_id', table_name='agents')
    op.drop_constraint('fk_agents_workspace_id', 'agents', type_='foreignkey')
    op.drop_column('agents', 'workspace_id')

    # Drop command_permissions table
    op.drop_table('command_permissions')

    # Drop workspace_api_keys table
    op.drop_table('workspace_api_keys')

    # Drop workspaces table
    op.drop_table('workspaces')
