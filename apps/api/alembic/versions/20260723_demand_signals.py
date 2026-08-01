"""demand_signals migration

Revision ID: 20260723_demand_signals
Revises: 20260723_sprint42
Create Date: 2026-07-23
"""

from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "20260723_demand_signals"
down_revision: str | None = "20260723_knowledge_graph"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "demand_signals",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("source", sa.String(50), nullable=False, index=True),
        sa.Column("source_url", sa.String(2048), server_default=""),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("author", sa.String(255), nullable=True),
        sa.Column("author_title", sa.String(255), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("pain_type", sa.String(100), nullable=True, index=True),
        sa.Column("urgency", sa.String(20), server_default="medium"),
        sa.Column("buying_intent", sa.Integer(), server_default="0"),
        sa.Column("lead_score", sa.Integer(), server_default="0", index=True),
        sa.Column("recommended_action", sa.String(50), server_default="monitor"),
        sa.Column("confidence", sa.Float(), server_default="0.5"),
        sa.Column("technologies", sa.Text(), nullable=True),
        sa.Column("keywords", sa.Text(), nullable=True),
        sa.Column("raw_data", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_ds_source", "demand_signals", ["source"])
    op.create_index("idx_ds_pain_type", "demand_signals", ["pain_type"])
    op.create_index("idx_ds_lead_score", "demand_signals", ["lead_score"])
    op.create_index("idx_ds_processed_at", "demand_signals", ["processed_at"])


def downgrade() -> None:
    op.drop_table("demand_signals")
