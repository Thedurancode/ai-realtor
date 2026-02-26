"""add_videogen_integration

Revision ID: 004_add_videogen
Revises: 003_add_postiz
Create Date: 2026-02-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005_add_videogen'
down_revision: Union[str, None] = None  # Standalone migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    # Create videogen_videos table
    op.create_table(
        'videogen_videos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=True),
        sa.Column('video_id', sa.String(length=100), nullable=False),
        sa.Column('avatar_id', sa.String(length=100), nullable=False),
        sa.Column('voice_id', sa.String(length=100), nullable=True),
        sa.Column('script', sa.Text(), nullable=False),
        sa.Column('script_type', sa.String(length=50), nullable=True, server_default='promotion'),
        sa.Column('video_url', sa.Text(), nullable=True),
        sa.Column('aspect_ratio', sa.String(length=10), nullable=True, server_default='16:9'),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('postiz_media_id', sa.String(length=100), nullable=True),
        sa.Column('postiz_media_url', sa.Text(), nullable=True),
        sa.Column('postiz_post_id', sa.String(length=100), nullable=True),
        sa.Column('platforms', sa.JSON(), nullable=True),
        sa.Column('platforms_posted', sa.JSON(), nullable=True),
        sa.Column('post_status', sa.String(length=50), nullable=True, server_default='pending'),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='processing'),
        sa.Column('generation_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('generation_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_videogen_videos_agent_id', 'videogen_videos', ['agent_id'])
    op.create_index('ix_videogen_videos_property_id', 'videogen_videos', ['property_id'])
    op.create_index('ix_videogen_videos_video_id', 'videogen_videos', ['video_id'])
    op.create_index('ix_videogen_videos_status', 'videogen_videos', ['status'])

    # Create videogen_avatars table
    op.create_table(
        'videogen_avatars',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('avatar_id', sa.String(length=100), nullable=False),
        sa.Column('avatar_name', sa.String(length=255), nullable=False),
        sa.Column('preview_image_url', sa.Text(), nullable=True),
        sa.Column('gender', sa.String(length=20), nullable=True),
        sa.Column('age', sa.String(length=20), nullable=True),
        sa.Column('ethnicity', sa.String(length=50), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('default_voice_id', sa.String(length=100), nullable=True),
        sa.Column('supported_languages', sa.JSON(), nullable=True),
        sa.Column('times_used', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('is_premium', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_videogen_avatars_avatar_id', 'videogen_avatars', ['avatar_id'])
    op.create_index('ix_videogen_avatars_is_active', 'videogen_avatars', ['is_active'])

    # Create videogen_script_templates table
    op.create_table(
        'videogen_script_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('template_name', sa.String(length=255), nullable=False),
        sa.Column('template_category', sa.String(length=50), nullable=False),
        sa.Column('template_type', sa.String(length=50), nullable=True, server_default='property'),
        sa.Column('script_template', sa.Text(), nullable=False),
        sa.Column('variables', sa.JSON(), nullable=True),
        sa.Column('default_avatar_id', sa.String(length=100), nullable=True),
        sa.Column('default_aspect_ratio', sa.String(length=10), nullable=True, server_default='16:9'),
        sa.Column('default_duration_target', sa.Integer(), nullable=True, server_default='60'),
        sa.Column('times_used', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_videogen_script_templates_agent_id', 'videogen_script_templates', ['agent_id'])
    op.create_index('ix_videogen_script_templates_template_category', 'videogen_script_templates', ['template_category'])

    # Create videogen_settings table
    op.create_table(
        'videogen_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('default_avatar_id', sa.String(length=100), nullable=True),
        sa.Column('default_voice_id', sa.String(length=100), nullable=True),
        sa.Column('default_aspect_ratio', sa.String(length=10), nullable=True, server_default='16:9'),
        sa.Column('default_background', sa.String(length=20), nullable=True, server_default='#FFFFFF'),
        sa.Column('auto_post_to_social', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('default_platforms', sa.JSON(), nullable=True),
        sa.Column('video_quality', sa.String(length=20), nullable=True, server_default='1080p'),
        sa.Column('use_branding', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('intro_text', sa.String(length=255), nullable=True),
        sa.Column('outro_text', sa.String(length=255), nullable=True),
        sa.Column('call_to_action', sa.String(length=255), nullable=True),
        sa.Column('api_key', sa.String(length=500), nullable=True),
        sa.Column('monthly_quota', sa.Integer(), nullable=True),
        sa.Column('videos_used_this_month', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('quota_reset_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agent_id')
    )


def downgrade() -> None:
    # Drop tables
    op.drop_table('videogen_settings')
    op.drop_table('videogen_script_templates')
    op.drop_table('videogen_avatars')
    op.drop_table('videogen_videos')
