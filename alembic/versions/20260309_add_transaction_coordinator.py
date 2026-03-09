"""Add transaction coordinator tables

Revision ID: 20260309_add_tc
Revises: e58e55272f67
Create Date: 2026-03-09
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20260309_add_tc'
down_revision: Union[str, None] = 'e58e55272f67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('property_id', sa.Integer(), sa.ForeignKey('properties.id'), nullable=False),
        sa.Column('offer_id', sa.Integer(), sa.ForeignKey('offers.id'), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='initiated'),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('accepted_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('attorney_review_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('inspection_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('appraisal_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('mortgage_contingency_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('title_clear_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('final_walkthrough_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closing_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sale_price', sa.Float(), nullable=True),
        sa.Column('earnest_money', sa.Float(), nullable=True),
        sa.Column('commission_rate', sa.Float(), nullable=True),
        sa.Column('financing_type', sa.String(), nullable=True),
        sa.Column('parties', sa.JSON(), server_default='[]'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('risk_flags', sa.JSON(), server_default='[]'),
        sa.Column('extra_data', sa.JSON(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_transactions_property_id', 'transactions', ['property_id'])
    op.create_index('ix_transactions_status', 'transactions', ['status'])
    op.create_index('ix_transactions_closing_date', 'transactions', ['closing_date'])

    op.create_table(
        'transaction_milestones',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('transaction_id', sa.Integer(), sa.ForeignKey('transactions.id'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('assigned_role', sa.String(50), nullable=True),
        sa.Column('assigned_name', sa.String(), nullable=True),
        sa.Column('assigned_contact', sa.String(), nullable=True),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reminder_sent', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('outcome_notes', sa.Text(), nullable=True),
        sa.Column('documents', sa.JSON(), server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_milestones_transaction_id', 'transaction_milestones', ['transaction_id'])
    op.create_index('ix_milestones_status', 'transaction_milestones', ['status'])
    op.create_index('ix_milestones_due_date', 'transaction_milestones', ['due_date'])


def downgrade() -> None:
    op.drop_table('transaction_milestones')
    op.drop_table('transactions')
