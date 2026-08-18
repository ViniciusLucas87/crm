"""Add isolated App Factory research and validation tables.

Revision ID: 20260818_app_factory
Revises: 20260818_reddit_leads
"""

import sqlalchemy as sa
from alembic import op

revision = "20260818_app_factory"
down_revision = "20260818_reddit_leads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("app_factory_candidates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("audience", sa.Text(), nullable=False),
        sa.Column("problem", sa.Text(), nullable=False),
        sa.Column("proposed_format", sa.String(40), nullable=False),
        sa.Column("proposed_price", sa.String(120), nullable=False),
        sa.Column("distribution_thesis", sa.Text(), nullable=False),
        sa.Column("current_workaround", sa.Text(), nullable=False),
        sa.Column("decision", sa.String(30), nullable=False, server_default="research"),
        sa.Column("decision_reason", sa.Text(), nullable=False),
        sa.Column("score_json", sa.Text(), nullable=False),
        sa.Column("total_score", sa.Integer(), nullable=False),
        sa.Column("estimated_monthly_cost_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("risk_level", sa.String(20), nullable=False, server_default="low"),
        sa.Column("evidence_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "slug", name="uq_app_factory_candidate_org_slug"),
    )
    op.create_index("ix_app_factory_candidate_org", "app_factory_candidates", ["organization_id", "decision", "total_score"])
    op.create_table("app_factory_evidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), sa.ForeignKey("app_factory_candidates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(40), nullable=False),
        sa.Column("source_title", sa.String(500), nullable=False),
        sa.Column("source_url", sa.String(1200), nullable=False),
        sa.Column("observed_at", sa.String(30), nullable=False),
        sa.Column("signal", sa.Text(), nullable=False),
        sa.Column("evidence_kind", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("candidate_id", "source_url", name="uq_app_factory_evidence_source"),
    )
    op.create_index("ix_app_factory_evidence_org", "app_factory_evidence", ["organization_id", "candidate_id"])
    op.create_table("app_factory_experiments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), sa.ForeignKey("app_factory_candidates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("hypothesis", sa.Text(), nullable=False),
        sa.Column("channel", sa.String(80), nullable=False),
        sa.Column("success_metric", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="proposed"),
        sa.Column("spend_limit_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("actual_spend_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("visitors", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("intent_actions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("paid_conversions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_app_factory_experiment_org", "app_factory_experiments", ["organization_id", "status"])


def downgrade() -> None:
    op.drop_table("app_factory_experiments")
    op.drop_table("app_factory_evidence")
    op.drop_table("app_factory_candidates")
