"""add_enhanced_video_generation

Enhanced property video generation system with:
- Agent video profiles (avatar + voice configuration)
- Property videos (orchestrated avatar + footage + assembly)
- PixVerse/Replicate integration for property footage
- FFmpeg assembly pipeline

Revision ID: 20260227_add_enhanced_video_generation
Revises: 20250227_add_property_websites
Create Date: 2026-02-27
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision: str = 'add_enhanced_video_generation'
down_revision: Union[str, None] = 'add_property_websites'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    # ===========================================================================
    # Create agent_video_profiles table
    # Stores agent avatar configuration and voice settings for enhanced videos
    # ===========================================================================
    op.create_table(
        'agent_video_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),

        # Avatar configuration
        sa.Column('headshot_url', sa.String(length=500), nullable=False),
        sa.Column('heygen_avatar_id', sa.String(length=100), unique=True, nullable=True),

        # Voice configuration
        sa.Column('voice_id', sa.String(length=100), nullable=False),
        sa.Column('voice_style', sa.String(length=50), server_default='professional', nullable=True),

        # Branding
        sa.Column('background_color', sa.String(length=7), server_default='#f8fafc', nullable=True),
        sa.Column('use_agent_branding', sa.Boolean(), server_default='true', nullable=True),

        # Scripts
        sa.Column('default_intro_script', sa.Text(), nullable=True),
        sa.Column('default_outro_script', sa.Text(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default='now()', nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate='now()'),

        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_agent_video_profiles_agent_id', 'agent_video_profiles', ['agent_id'], unique=True)
    op.create_index('ix_agent_video_profiles_heygen_avatar_id', 'agent_video_profiles', ['heygen_avatar_id'])

    # ===========================================================================
    # Create property_videos table
    # Tracks enhanced videos with avatar + property footage + assembly
    # ===========================================================================
    op.create_table(
        'property_videos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=False),

        # Video configuration
        sa.Column('video_type', sa.String(length=50), nullable=False),  # ENUM: property_tour, agent_intro, market_update, just_sold, new_listing
        sa.Column('style', sa.String(length=50), server_default='luxury', nullable=True),  # luxury, friendly, professional
        sa.Column('duration_target', sa.Integer(), server_default='60', nullable=False),

        # Generated content
        sa.Column('generated_script', sa.Text(), nullable=False),
        sa.Column('voiceover_url', sa.String(length=500), nullable=True),

        # Avatar videos
        sa.Column('intro_video_url', sa.String(length=500), nullable=True),
        sa.Column('outro_video_url', sa.String(length=500), nullable=True),

        # Property footage
        sa.Column('property_clips', postgresql.JSON(), nullable=True),  # Array of PixVerse video URLs
        sa.Column('photos_used', postgresql.JSON(), nullable=True),  # Array of photo URLs used

        # Final video
        sa.Column('final_video_url', sa.String(length=500), nullable=True),
        sa.Column('thumbnail_url', sa.String(length=500), nullable=True),

        # Metadata
        sa.Column('duration', sa.Float(), nullable=True),  # Actual duration in seconds
        sa.Column('resolution', sa.String(length=20), server_default='1080p', nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),  # Size in bytes

        # Generation tracking
        sa.Column('status', sa.String(length=50), server_default='draft', nullable=False),  # ENUM: draft, generating_script, script_completed, generating_voiceover, voiceover_completed, generating_intro, intro_completed, generating_footage, footage_completed, assembling_video, completed, failed
        sa.Column('generation_steps', postgresql.JSON(), nullable=True),  # Track each step's status
        sa.Column('error_message', sa.Text(), nullable=True),

        # Cost tracking
        sa.Column('generation_cost', sa.Float(), nullable=True),  # Total cost in USD
        sa.Column('cost_breakdown', postgresql.JSON(), nullable=True),  # {heygen: 2.00, pixverse: 0.05, elevenlabs: 0.03}

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default='now()', nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate='now()'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),

        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_property_videos_agent_id', 'property_videos', ['agent_id'])
    op.create_index('ix_property_videos_property_id', 'property_videos', ['property_id'])
    op.create_index('ix_property_videos_status', 'property_videos', ['status'])
    op.create_index('ix_property_videos_video_type', 'property_videos', ['video_type'])


def downgrade() -> None:
    # Drop tables
    op.drop_table('property_videos')
    op.drop_table('agent_video_profiles')
