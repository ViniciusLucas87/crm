"""expand lead intelligence workspace

Revision ID: 20260721_0004
Revises: 20260721_0003
Create Date: 2026-07-21
"""

from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "20260721_0004"
down_revision: str | None = "20260721_0003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # ── Expand leads table ──
    op.add_column("leads", sa.Column("tags", sa.Text(), nullable=True))
    op.add_column("leads", sa.Column("executive_summary", sa.Text(), nullable=True))
    op.add_column("leads", sa.Column("research_stages", sa.Text(), nullable=True))
    op.add_column("leads", sa.Column("decision_makers_data", sa.Text(), nullable=True))
    op.add_column("leads", sa.Column("outreach_data", sa.Text(), nullable=True))
    op.add_column("leads", sa.Column("estimated_deal_low", sa.Integer(), nullable=True))
    op.add_column("leads", sa.Column("estimated_deal_high", sa.Integer(), nullable=True))
    op.add_column("leads", sa.Column("technology_maturity", sa.String(30), nullable=True))
    op.add_column("leads", sa.Column("last_researched_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("leads", sa.Column("revenue_estimate", sa.String(50), nullable=True))
    op.add_column("leads", sa.Column("linkedin_url", sa.String(500), nullable=True))
    op.add_column("leads", sa.Column("country", sa.String(120), nullable=True))

    # ── Saved searches ──
    op.create_table("saved_searches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("filters_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_saved_searches_org", "saved_searches", ["organization_id"])

    # ── Lead timeline events ──
    op.create_table("lead_timeline_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_lead_timeline_lead", "lead_timeline_events", ["lead_id"])
    op.create_index("ix_lead_timeline_org", "lead_timeline_events", ["organization_id"])


def downgrade() -> None:
    op.drop_table("lead_timeline_events")
    op.drop_table("saved_searches")
    op.drop_column("leads", "country")
    op.drop_column("leads", "linkedin_url")
    op.drop_column("leads", "revenue_estimate")
    op.drop_column("leads", "last_researched_at")
    op.drop_column("leads", "technology_maturity")
    op.drop_column("leads", "estimated_deal_high")
    op.drop_column("leads", "estimated_deal_low")
    op.drop_column("leads", "outreach_data")
    op.drop_column("leads", "decision_makers_data")
    op.drop_column("leads", "research_stages")
    op.drop_column("leads", "executive_summary")
    op.drop_column("leads", "tags")
