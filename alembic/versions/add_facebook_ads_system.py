"""add_facebook_ads_system

Revision ID: 002_add_facebook_ads
Revises: 001_add_agent_brand
Create Date: 2026-02-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_facebook_ads'
down_revision: Union[str, None] = '001_add_agent_brand'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create facebook_campaigns table
    op.create_table(
        'facebook_campaigns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=True),
        sa.Column('campaign_name', sa.String(length=255), nullable=False),
        sa.Column('campaign_objective', sa.String(length=100), nullable=False),
        sa.Column('campaign_status', sa.String(length=50), nullable=True, server_default='draft'),
        sa.Column('targeting_audience', sa.JSON(), nullable=True),
        sa.Column('targeting_custom_audiences', sa.JSON(), nullable=True),
        sa.Column('targeting_lookalike', sa.JSON(), nullable=True),
        sa.Column('daily_budget', sa.Float(), nullable=True),
        sa.Column('lifetime_budget', sa.Float(), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('ad_creatives', sa.JSON(), nullable=True),
        sa.Column('ad_copy', sa.JSON(), nullable=True),
        sa.Column('ad_format', sa.String(length=50), nullable=True, server_default='single_image'),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('generated_by', sa.String(length=50), nullable=True, server_default='ai'),
        sa.Column('generation_model', sa.String(length=100), nullable=True),
        sa.Column('campaign_id_meta', sa.String(length=100), nullable=True),
        sa.Column('metrics', sa.JSON(), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('review_insights', sa.JSON(), nullable=True),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('key_phrases', sa.JSON(), nullable=True),
        sa.Column('competitor_analysis', sa.JSON(), nullable=True),
        sa.Column('competitor_spend_patterns', sa.JSON(), nullable=True),
        sa.Column('meta_access_token', sa.String(length=500), nullable=True),
        sa.Column('auto_launch', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('launch_config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_facebook_campaigns_agent_id', 'facebook_campaigns', ['agent_id'])
    op.create_index('ix_facebook_campaigns_property_id', 'facebook_campaigns', ['property_id'])
    op.create_index('ix_facebook_campaigns_campaign_status', 'facebook_campaigns', ['campaign_status'])

    # Create facebook_ad_sets table
    op.create_table(
        'facebook_ad_sets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('ad_set_name', sa.String(length=255), nullable=False),
        sa.Column('targeting', sa.JSON(), nullable=True),
        sa.Column('optimization_goal', sa.String(length=100), nullable=True),
        sa.Column('billing_event', sa.String(length=50), nullable=True),
        sa.Column('bid_strategy', sa.String(length=50), nullable=True),
        sa.Column('daily_budget', sa.Float(), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=True),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('ad_set_id_meta', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['campaign_id'], ['facebook_campaigns.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_facebook_ad_sets_campaign_id', 'facebook_ad_sets', ['campaign_id'])

    # Create facebook_creatives table
    op.create_table(
        'facebook_creatives',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('creative_name', sa.String(length=255), nullable=False),
        sa.Column('creative_format', sa.String(length=50), nullable=False),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('video_url', sa.String(length=500), nullable=True),
        sa.Column('carousel_items', sa.JSON(), nullable=True),
        sa.Column('primary_text', sa.Text(), nullable=True),
        sa.Column('headline', sa.String(length=255), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('call_to_action', sa.String(length=50), nullable=True),
        sa.Column('dynamic_creative_options', sa.JSON(), nullable=True),
        sa.Column('creative_id_meta', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['campaign_id'], ['facebook_campaigns.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_facebook_creatives_campaign_id', 'facebook_creatives', ['campaign_id'])

    # Create market_research table
    op.create_table(
        'market_research',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('research_name', sa.String(length=255), nullable=False),
        sa.Column('market_location', sa.JSON(), nullable=True),
        sa.Column('market_niche', sa.String(length=255), nullable=True),
        sa.Column('audience_size_estimate', sa.Integer(), nullable=True),
        sa.Column('audience_demographics', sa.JSON(), nullable=True),
        sa.Column('audience_interests', sa.JSON(), nullable=True),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('keyword_search_volume', sa.JSON(), nullable=True),
        sa.Column('market_positioning', sa.JSON(), nullable=True),
        sa.Column('competitor_positioning', sa.JSON(), nullable=True),
        sa.Column('seasonal_trends', sa.JSON(), nullable=True),
        sa.Column('price_sensitivity', sa.JSON(), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_market_research_agent_id', 'market_research', ['agent_id'])

    # Create competitor_analyses table
    op.create_table(
        'competitor_analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('competitor_name', sa.String(length=255), nullable=True),
        sa.Column('competitor_domain', sa.String(length=500), nullable=True),
        sa.Column('active_ads_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('ad_spend_estimate', sa.Float(), nullable=True),
        sa.Column('ad_frequency', sa.Float(), nullable=True),
        sa.Column('top_performing_creatives', sa.JSON(), nullable=True),
        sa.Column('creative_themes', sa.JSON(), nullable=True),
        sa.Column('copy_patterns', sa.JSON(), nullable=True),
        sa.Column('suspected_audiences', sa.JSON(), nullable=True),
        sa.Column('targeting_patterns', sa.JSON(), nullable=True),
        sa.Column('landing_pages', sa.JSON(), nullable=True),
        sa.Column('funnel_structure', sa.JSON(), nullable=True),
        sa.Column('analyzed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_competitor_analyses_agent_id', 'competitor_analyses', ['agent_id'])

    # Create review_intelligence table
    op.create_table(
        'review_intelligence',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('overall_sentiment', sa.String(length=20), nullable=True),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('sentiment_distribution', sa.JSON(), nullable=True),
        sa.Column('key_phrases', sa.JSON(), nullable=True),
        sa.Column('pain_points', sa.JSON(), nullable=True),
        sa.Column('selling_points', sa.JSON(), nullable=True),
        sa.Column('questions_asked', sa.JSON(), nullable=True),
        sa.Column('total_reviews', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('average_rating', sa.Float(), nullable=True),
        sa.Column('rating_distribution', sa.JSON(), nullable=True),
        sa.Column('recommended_hooks', sa.JSON(), nullable=True),
        sa.Column('recommended_ctas', sa.JSON(), nullable=True),
        sa.Column('recommended_themes', sa.JSON(), nullable=True),
        sa.Column('extracted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_review_intelligence_agent_id', 'review_intelligence', ['agent_id'])
    op.create_index('ix_review_intelligence_property_id', 'review_intelligence', ['property_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_review_intelligence_property_id', table_name='review_intelligence')
    op.drop_index('ix_review_intelligence_agent_id', table_name='review_intelligence')
    op.drop_index('ix_competitor_analyses_agent_id', table_name='competitor_analyses')
    op.drop_index('ix_market_research_agent_id', table_name='market_research')
    op.drop_index('ix_facebook_creatives_campaign_id', table_name='facebook_creatives')
    op.drop_index('ix_facebook_ad_sets_campaign_id', table_name='facebook_ad_sets')
    op.drop_index('ix_facebook_campaigns_campaign_status', table_name='facebook_campaigns')
    op.drop_index('ix_facebook_campaigns_property_id', table_name='facebook_campaigns')
    op.drop_index('ix_facebook_campaigns_agent_id', table_name='facebook_campaigns')

    # Drop tables
    op.drop_table('review_intelligence')
    op.drop_table('competitor_analyses')
    op.drop_table('market_research')
    op.drop_table('facebook_creatives')
    op.drop_table('facebook_ad_sets')
    op.drop_table('facebook_campaigns')
