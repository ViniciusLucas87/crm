"""Add reusable social lead campaigns and Reddit opportunities.

Revision ID: 20260818_reddit_leads
Revises: 20260817_customer_management
"""

import sqlalchemy as sa

from alembic import op

revision = "20260818_reddit_leads"
down_revision = "20260817_customer_management"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "social_lead_campaigns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("channel", sa.String(30), nullable=False, server_default="reddit"),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("product_code", sa.String(80), nullable=False),
        sa.Column("audience", sa.Text(), nullable=False),
        sa.Column("communities_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("pain_signals_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("offer_summary", sa.Text(), nullable=False),
        sa.Column("public_reply_guidance", sa.Text(), nullable=False),
        sa.Column("dm_guidance", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_social_campaign_org", "social_lead_campaigns", ["organization_id", "status"]
    )
    op.create_index("ix_social_campaign_product", "social_lead_campaigns", ["product_code"])

    op.create_table(
        "social_lead_opportunities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column(
            "campaign_id",
            sa.Integer(),
            sa.ForeignKey("social_lead_campaigns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("channel", sa.String(30), nullable=False, server_default="reddit"),
        sa.Column("external_id", sa.String(120), nullable=True),
        sa.Column("community", sa.String(120), nullable=False),
        sa.Column("author_handle", sa.String(120), nullable=False),
        sa.Column("post_title", sa.String(500), nullable=False),
        sa.Column("post_excerpt", sa.Text(), nullable=False),
        sa.Column("source_url", sa.String(1000), nullable=False),
        sa.Column("relevance_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("relevance_reason", sa.Text(), nullable=False),
        sa.Column("detected_signals_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(40), nullable=False, server_default="watch"),
        sa.Column("public_reply_draft", sa.Text(), nullable=True),
        sa.Column("dm_draft", sa.Text(), nullable=True),
        sa.Column("permission_basis", sa.Text(), nullable=True),
        sa.Column("human_approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("contacted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("response_summary", sa.Text(), nullable=True),
        sa.Column("next_follow_up_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("owner_user_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "source_url", name="uq_social_lead_source_per_org"),
    )
    op.create_index(
        "ix_social_opportunity_queue",
        "social_lead_opportunities",
        ["organization_id", "status", "relevance_score"],
    )
    op.create_index("ix_social_opportunity_campaign", "social_lead_opportunities", ["campaign_id"])
    op.create_index("ix_social_opportunity_author", "social_lead_opportunities", ["author_handle"])


def downgrade() -> None:
    op.drop_table("social_lead_opportunities")
    op.drop_table("social_lead_campaigns")
