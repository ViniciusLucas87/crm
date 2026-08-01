"""knowledge_graph migration

Revision ID: 20260723_knowledge_graph
Revises: 20260723_sprint42
Create Date: 2026-07-23
"""

from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "20260723_knowledge_graph"
down_revision: str | None = "20260723_sprint42"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "knowledge_facts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("uuid", sa.String(36), unique=True, nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("value_type", sa.String(20), server_default="string"),
        sa.Column("source", sa.String(50), nullable=False, server_default="manual"),
        sa.Column("source_detail", sa.String(255), nullable=True),
        sa.Column("confidence", sa.Float(), default=0.5),
        sa.Column("verified", sa.Boolean(), default=False),
        sa.Column("verified_by", sa.String(255), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("manual_override", sa.Boolean(), default=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("updated_by", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_kf_entity", "knowledge_facts", ["entity_type", "entity_id"])
    op.create_index("idx_kf_key", "knowledge_facts", ["key"])
    op.create_index("idx_kf_confidence", "knowledge_facts", ["confidence"])
    op.create_unique_constraint("uq_entity_fact", "knowledge_facts", ["entity_type", "entity_id", "key"])

    op.create_table(
        "knowledge_fact_history",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("fact_id", sa.Integer(), sa.ForeignKey("knowledge_facts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("previous_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=False),
        sa.Column("previous_confidence", sa.Float(), nullable=True),
        sa.Column("new_confidence", sa.Float(), default=0.5),
        sa.Column("previous_source", sa.String(50), nullable=True),
        sa.Column("new_source", sa.String(50), nullable=False),
        sa.Column("changed_by", sa.String(255), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_kfh_fact", "knowledge_fact_history", ["fact_id"])

    op.create_table(
        "knowledge_relationships",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("uuid", sa.String(36), unique=True, nullable=False),
        sa.Column("from_type", sa.String(50), nullable=False),
        sa.Column("from_id", sa.Integer(), nullable=False),
        sa.Column("relationship_type", sa.String(50), nullable=False),
        sa.Column("to_type", sa.String(50), nullable=False),
        sa.Column("to_id", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Float(), default=0.5),
        sa.Column("source", sa.String(50), server_default="manual"),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_kr_from", "knowledge_relationships", ["from_type", "from_id"])
    op.create_index("idx_kr_to", "knowledge_relationships", ["to_type", "to_id"])
    op.create_index("idx_kr_rel_type", "knowledge_relationships", ["relationship_type"])
    op.create_unique_constraint("uq_relationship", "knowledge_relationships", ["from_type", "from_id", "to_type", "to_id", "relationship_type"])

    op.create_table(
        "knowledge_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("uuid", sa.String(36), unique=True, nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("actor_type", sa.String(20), server_default="system"),
        sa.Column("actor_id", sa.String(255), nullable=True),
        sa.Column("organization_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_ke_entity", "knowledge_events", ["entity_type", "entity_id"])
    op.create_index("idx_ke_type", "knowledge_events", ["event_type"])
    op.create_index("idx_ke_created", "knowledge_events", ["created_at"])


def downgrade() -> None:
    op.drop_table("knowledge_events")
    op.drop_table("knowledge_relationships")
    op.drop_table("knowledge_fact_history")
    op.drop_table("knowledge_facts")
