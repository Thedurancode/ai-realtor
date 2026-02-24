"""add_postiz_integration

Revision ID: 003_add_postiz
Revises: 002_add_facebook_ads
Create Date: 2026-02-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_add_postiz'
down_revision: Union[str, None] = '002_add_facebook_ads'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create postiz_accounts table
    op.create_table(
        'postiz_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('api_key', sa.String(length=500), nullable=False),
        sa.Column('workspace_id', sa.String(length=100), nullable=True),
        sa.Column('account_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('connected_platforms', sa.JSON(), nullable=True),
        sa.Column('platform_tokens', sa.JSON(), nullable=True),
        sa.Column('default_timezone', sa.String(length=50), nullable=True, server_default='America/New_York'),
        sa.Column('auto_publish', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('notify_on_publish', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_postiz_accounts_agent_id', 'postiz_accounts', ['agent_id'])

    # Create postiz_posts table
    op.create_table(
        'postiz_posts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=True),
        sa.Column('content_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('caption', sa.Text(), nullable=False),
        sa.Column('hashtags', sa.JSON(), nullable=True),
        sa.Column('mention_accounts', sa.JSON(), nullable=True),
        sa.Column('media_urls', sa.JSON(), nullable=True),
        sa.Column('media_type', sa.String(length=50), nullable=True, server_default='image'),
        sa.Column('thumbnail_url', sa.String(length=500), nullable=True),
        sa.Column('platform_content', sa.JSON(), nullable=True),
        sa.Column('platform_optimizations', sa.JSON(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scheduled_timezone', sa.String(length=50), nullable=True, server_default='America/New_York'),
        sa.Column('publish_immediately', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('target_audience', sa.JSON(), nullable=True),
        sa.Column('boost_post', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('boost_budget', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='draft'),
        sa.Column('post_id_postiz', sa.String(length=100), nullable=True),
        sa.Column('post_ids_platforms', sa.JSON(), nullable=True),
        sa.Column('analytics', sa.JSON(), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('generated_by', sa.String(length=50), nullable=True, server_default='ai'),
        sa.Column('generation_model', sa.String(length=100), nullable=True),
        sa.Column('ai_prompt', sa.Text(), nullable=True),
        sa.Column('use_branding', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('brand_applied', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.ForeignKeyConstraint(['account_id'], ['postiz_accounts.id'], ),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_postiz_posts_agent_id', 'postiz_posts', ['agent_id'])
    op.create_index('ix_postiz_posts_account_id', 'postiz_posts', ['account_id'])
    op.create_index('ix_postiz_posts_property_id', 'postiz_posts', ['property_id'])
    op.create_index('ix_postiz_posts_status', 'postiz_posts', ['status'])
    op.create_index('ix_postiz_posts_scheduled_at', 'postiz_posts', ['scheduled_at'])

    # Create postiz_calendars table
    op.create_table(
        'postiz_calendars',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('calendar_name', sa.String(length=255), nullable=False),
        sa.Column('calendar_type', sa.String(length=50), nullable=True, server_default='marketing'),
        sa.Column('posting_frequency', sa.JSON(), nullable=True),
        sa.Column('best_times_to_post', sa.JSON(), nullable=True),
        sa.Column('content_mix', sa.JSON(), nullable=True),
        sa.Column('auto_schedule_properties', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('auto_schedule_market_reports', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('auto_schedule_open_houses', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('default_timezone', sa.String(length=50), nullable=True, server_default='America/New_York'),
        sa.Column('queue_capacity', sa.Integer(), nullable=True, server_default='30'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_postiz_calendars_agent_id', 'postiz_calendars', ['agent_id'])

    # Create postiz_templates table
    op.create_table(
        'postiz_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('template_name', sa.String(length=255), nullable=False),
        sa.Column('template_category', sa.String(length=100), nullable=False),
        sa.Column('template_type', sa.String(length=50), nullable=True, server_default='property'),
        sa.Column('caption_template', sa.Text(), nullable=False),
        sa.Column('hashtag_template', sa.JSON(), nullable=True),
        sa.Column('mention_template', sa.JSON(), nullable=True),
        sa.Column('media_type', sa.String(length=50), nullable=True, server_default='image'),
        sa.Column('media_count', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('media_guidance', sa.Text(), nullable=True),
        sa.Column('platform_variations', sa.JSON(), nullable=True),
        sa.Column('ai_generate_caption', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('ai_optimize_for_platform', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('times_used', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_postiz_templates_agent_id', 'postiz_templates', ['agent_id'])
    op.create_index('ix_postiz_templates_template_category', 'postiz_templates', ['template_category'])

    # Create postiz_analytics table
    op.create_table(
        'postiz_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_type', sa.String(length=20), nullable=False),
        sa.Column('metrics', sa.JSON(), nullable=True),
        sa.Column('top_posts', sa.JSON(), nullable=True),
        sa.Column('top_hashtags', sa.JSON(), nullable=True),
        sa.Column('top_times', sa.JSON(), nullable=True),
        sa.Column('audience_demographics', sa.JSON(), nullable=True),
        sa.Column('audience_growth', sa.JSON(), nullable=True),
        sa.Column('content_type_performance', sa.JSON(), nullable=True),
        sa.Column('media_type_performance', sa.JSON(), nullable=True),
        sa.Column('engagement_by_day', sa.JSON(), nullable=True),
        sa.Column('engagement_by_platform', sa.JSON(), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_postiz_analytics_agent_id', 'postiz_analytics', ['agent_id'])

    # Create postiz_campaigns table
    op.create_table(
        'postiz_campaigns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=True),
        sa.Column('campaign_name', sa.String(length=255), nullable=False),
        sa.Column('campaign_type', sa.String(length=50), nullable=False),
        sa.Column('campaign_status', sa.String(length=50), nullable=True, server_default='draft'),
        sa.Column('target_impressions', sa.Integer(), nullable=True),
        sa.Column('target_engagement_rate', sa.Float(), nullable=True),
        sa.Column('target_clicks', sa.Integer(), nullable=True),
        sa.Column('target_leads', sa.Integer(), nullable=True),
        sa.Column('posts', sa.JSON(), nullable=True),
        sa.Column('post_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_budget', sa.Float(), nullable=True),
        sa.Column('spent_budget', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('metrics', sa.JSON(), nullable=True),
        sa.Column('goal_progress', sa.JSON(), nullable=True),
        sa.Column('auto_generate_content', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('auto_optimize_schedule', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_postiz_campaigns_agent_id', 'postiz_campaigns', ['agent_id'])
    op.create_index('ix_postiz_campaigns_property_id', 'postiz_campaigns', ['property_id'])
    op.create_index('ix_postiz_campaigns_campaign_status', 'postiz_campaigns', ['campaign_status'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_postiz_campaigns_campaign_status', table_name='postiz_campaigns')
    op.drop_index('ix_postiz_campaigns_property_id', table_name='postiz_campaigns')
    op.drop_index('ix_postiz_campaigns_agent_id', table_name='postiz_campaigns')
    op.drop_index('ix_postiz_analytics_agent_id', table_name='postiz_analytics')
    op.drop_index('ix_postiz_templates_template_category', table_name='postiz_templates')
    op.drop_index('ix_postiz_templates_agent_id', table_name='postiz_templates')
    op.drop_index('ix_postiz_calendars_agent_id', table_name='postiz_calendars')
    op.drop_index('ix_postiz_posts_scheduled_at', table_name='postiz_posts')
    op.drop_index('ix_postiz_posts_status', table_name='postiz_posts')
    op.drop_index('ix_postiz_posts_property_id', table_name='postiz_posts')
    op.drop_index('ix_postiz_posts_account_id', table_name='postiz_posts')
    op.drop_index('ix_postiz_posts_agent_id', table_name='postiz_posts')
    op.drop_index('ix_postiz_accounts_agent_id', table_name='postiz_accounts')

    # Drop tables
    op.drop_table('postiz_campaigns')
    op.drop_table('postiz_analytics')
    op.drop_table('postiz_templates')
    op.drop_table('postiz_calendars')
    op.drop_table('postiz_posts')
    op.drop_table('postiz_accounts')
