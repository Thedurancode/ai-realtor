"""Add intelligence and learning models

Revision ID: 20250222_add_intelligence
Revises: c8d2e4f5a7b9
Create Date: 2026-02-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250222_add_intelligence'
down_revision = 'c8d2e4f5a7b9'
branch_labels = None
depends_on = None


def upgrade():
    # Create deal_outcomes table
    op.create_table(
        'deal_outcomes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('closed_won', 'closed_lost', 'withdrawn', 'stalled', 'active', name='outcomestatus'), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('days_to_close', sa.Integer(), nullable=True),
        sa.Column('final_sale_price', sa.Float(), nullable=True),
        sa.Column('original_list_price', sa.Float(), nullable=True),
        sa.Column('price_reduction_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('predicted_probability', sa.Float(), nullable=True),
        sa.Column('predicted_days_to_close', sa.Integer(), nullable=True),
        sa.Column('prediction_confidence', sa.String(length=20), nullable=True),
        sa.Column('feature_snapshot', postgresql.JSON(), nullable=True),
        sa.Column('outcome_reason', sa.String(), nullable=True),
        sa.Column('lessons_learned', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_deal_outcomes_agent_id'), 'deal_outcomes', ['agent_id'], unique=False)
    op.create_index(op.f('ix_deal_outcomes_id'), 'deal_outcomes', ['id'], unique=False)
    op.create_index(op.f('ix_deal_outcomes_property_id'), 'deal_outcomes', ['property_id'], unique=False)

    # Create agent_performance_metrics table
    op.create_table(
        'agent_performance_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('period_type', sa.String(length=10), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total_deals', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('closed_deals', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('closed_won', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('closing_rate', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('total_volume', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('average_deal_size', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('total_profit', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('average_days_to_close', sa.Float(), nullable=True),
        sa.Column('average_deal_score', sa.Float(), nullable=True),
        sa.Column('best_property_types', postgresql.JSON(), nullable=True),
        sa.Column('best_cities', postgresql.JSON(), nullable=True),
        sa.Column('best_price_ranges', postgresql.JSON(), nullable=True),
        sa.Column('success_patterns', postgresql.JSON(), nullable=True),
        sa.Column('failure_patterns', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_performance_metrics_agent_id'), 'agent_performance_metrics', ['agent_id'], unique=False)
    op.create_index(op.f('ix_agent_performance_metrics_id'), 'agent_performance_metrics', ['id'], unique=False)

    # Create prediction_logs table
    op.create_table(
        'prediction_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('predicted_probability', sa.Float(), nullable=False),
        sa.Column('predicted_days', sa.Integer(), nullable=False),
        sa.Column('confidence', sa.String(length=20), nullable=False),
        sa.Column('deal_score', sa.Float(), nullable=True),
        sa.Column('completion_rate', sa.Float(), nullable=True),
        sa.Column('has_contacts', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('has_skip_trace', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('activity_velocity', sa.Float(), nullable=True),
        sa.Column('feature_snapshot', postgresql.JSON(), nullable=True),
        sa.Column('actual_outcome', sa.Enum('closed_won', 'closed_lost', 'withdrawn', 'stalled', 'active', name='outcomestatus'), nullable=True),
        sa.Column('actual_days_to_close', sa.Integer(), nullable=True),
        sa.Column('probability_error', sa.Float(), nullable=True),
        sa.Column('was_correct_direction', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('outcome_recorded_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prediction_logs_id'), 'prediction_logs', ['id'], unique=False)
    op.create_index(op.f('ix_prediction_logs_property_id'), 'prediction_logs', ['property_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_prediction_logs_property_id'), table_name='prediction_logs')
    op.drop_index(op.f('ix_prediction_logs_id'), table_name='prediction_logs')
    op.drop_table('prediction_logs')

    op.drop_index(op.f('ix_agent_performance_metrics_id'), table_name='agent_performance_metrics')
    op.drop_index(op.f('ix_agent_performance_metrics_agent_id'), table_name='agent_performance_metrics')
    op.drop_table('agent_performance_metrics')

    op.drop_index(op.f('ix_deal_outcomes_property_id'), table_name='deals_outcomes')
    op.drop_index(op.f('ix_deal_outcomes_id'), table_name='deal_outcomes')
    op.drop_index(op.f('ix_deal_outcomes_agent_id'), table_name='deal_outcomes')
    op.drop_table('deal_outcomes')
