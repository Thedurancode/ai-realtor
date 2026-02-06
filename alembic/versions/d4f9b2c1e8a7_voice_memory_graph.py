"""voice memory graph

Revision ID: d4f9b2c1e8a7
Revises: c1a5f8c7b901
Create Date: 2026-02-06 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d4f9b2c1e8a7"
down_revision: Union[str, None] = "c1a5f8c7b901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "voice_memory_nodes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(length=128), nullable=False),
        sa.Column("node_type", sa.String(length=64), nullable=False),
        sa.Column("node_key", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.String(length=512), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("importance", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "node_type", "node_key", name="uq_voice_memory_node"),
    )
    op.create_index(op.f("ix_voice_memory_nodes_id"), "voice_memory_nodes", ["id"], unique=False)
    op.create_index(op.f("ix_voice_memory_nodes_session_id"), "voice_memory_nodes", ["session_id"], unique=False)
    op.create_index(op.f("ix_voice_memory_nodes_node_type"), "voice_memory_nodes", ["node_type"], unique=False)
    op.create_index(op.f("ix_voice_memory_nodes_node_key"), "voice_memory_nodes", ["node_key"], unique=False)
    op.create_index(op.f("ix_voice_memory_nodes_last_seen_at"), "voice_memory_nodes", ["last_seen_at"], unique=False)
    op.create_index("ix_voice_memory_nodes_session_type", "voice_memory_nodes", ["session_id", "node_type"], unique=False)

    op.create_table(
        "voice_memory_edges",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(length=128), nullable=False),
        sa.Column("source_node_id", sa.Integer(), nullable=False),
        sa.Column("target_node_id", sa.Integer(), nullable=False),
        sa.Column("relation", sa.String(length=64), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["source_node_id"], ["voice_memory_nodes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_node_id"], ["voice_memory_nodes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "source_node_id", "target_node_id", "relation", name="uq_voice_memory_edge"),
    )
    op.create_index(op.f("ix_voice_memory_edges_id"), "voice_memory_edges", ["id"], unique=False)
    op.create_index(op.f("ix_voice_memory_edges_session_id"), "voice_memory_edges", ["session_id"], unique=False)
    op.create_index(op.f("ix_voice_memory_edges_relation"), "voice_memory_edges", ["relation"], unique=False)
    op.create_index(op.f("ix_voice_memory_edges_last_seen_at"), "voice_memory_edges", ["last_seen_at"], unique=False)
    op.create_index("ix_voice_memory_edges_session_relation", "voice_memory_edges", ["session_id", "relation"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_voice_memory_edges_session_relation", table_name="voice_memory_edges")
    op.drop_index(op.f("ix_voice_memory_edges_last_seen_at"), table_name="voice_memory_edges")
    op.drop_index(op.f("ix_voice_memory_edges_relation"), table_name="voice_memory_edges")
    op.drop_index(op.f("ix_voice_memory_edges_session_id"), table_name="voice_memory_edges")
    op.drop_index(op.f("ix_voice_memory_edges_id"), table_name="voice_memory_edges")
    op.drop_table("voice_memory_edges")

    op.drop_index("ix_voice_memory_nodes_session_type", table_name="voice_memory_nodes")
    op.drop_index(op.f("ix_voice_memory_nodes_last_seen_at"), table_name="voice_memory_nodes")
    op.drop_index(op.f("ix_voice_memory_nodes_node_key"), table_name="voice_memory_nodes")
    op.drop_index(op.f("ix_voice_memory_nodes_node_type"), table_name="voice_memory_nodes")
    op.drop_index(op.f("ix_voice_memory_nodes_session_id"), table_name="voice_memory_nodes")
    op.drop_index(op.f("ix_voice_memory_nodes_id"), table_name="voice_memory_nodes")
    op.drop_table("voice_memory_nodes")
