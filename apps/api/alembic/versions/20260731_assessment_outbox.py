"""Add automation_assessments + outbox_events tables

Revision ID: 20260731_assessment_outbox
Create Date: 2026-07-31
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260731_assessment_outbox"
down_revision: Union[str, None] = "20260723_worker_runtime"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "automation_assessments",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("public_id", sa.String(36), nullable=False, unique=True, index=True),
        sa.Column("organization_id", sa.Integer(), nullable=False, index=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("contact_id", sa.Integer(), sa.ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("lead_id", sa.Integer(), sa.ForeignKey("leads.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("assessment_version", sa.String(20), nullable=False),
        sa.Column("scoring_model_version", sa.String(20), server_default="1.0"),
        sa.Column("recommendation_model_version", sa.String(20), server_default="1.0"),
        sa.Column("raw_answers", postgresql.JSONB(), nullable=False),
        sa.Column("calculated_output", postgresql.JSONB(), nullable=False),
        sa.Column("industry", sa.String(120), nullable=True),
        sa.Column("employee_range", sa.String(50), nullable=True),
        sa.Column("automation_score", sa.Integer(), server_default="0"),
        sa.Column("estimated_annual_savings", sa.Integer(), server_default="0"),
        sa.Column("estimated_weekly_hours", sa.Integer(), server_default="0"),
        sa.Column("estimated_annual_hours", sa.Integer(), server_default="0"),
        sa.Column("estimated_people_count", sa.Integer(), server_default="0"),
        sa.Column("primary_pain_points", postgresql.JSONB(), nullable=True),
        sa.Column("privacy_accepted", sa.Boolean(), server_default="false"),
        sa.Column("marketing_accepted", sa.Boolean(), server_default="false"),
        sa.Column("consent_accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("utm_source", sa.String(120), nullable=True),
        sa.Column("utm_medium", sa.String(120), nullable=True),
        sa.Column("utm_campaign", sa.String(120), nullable=True),
        sa.Column("referrer", sa.String(500), nullable=True),
        sa.Column("landing_page", sa.String(500), nullable=True),
        sa.Column("idempotency_key", sa.String(100), nullable=True, unique=True),
        sa.Column("assessment_fingerprint", sa.String(64), nullable=True, index=True),
        sa.Column("pdf_status", sa.String(20), server_default="pending"),
        sa.Column("pdf_storage_key", sa.String(500), nullable=True),
        sa.Column("pdf_generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("correlation_id", sa.String(64), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "outbox_events",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("event_type", sa.String(80), nullable=False, index=True),
        sa.Column("payload_json", postgresql.JSONB(), nullable=False),
        sa.Column("correlation_id", sa.String(64), nullable=True, index=True),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False, index=True),
        sa.Column("attempt_count", sa.Integer(), server_default="0"),
        sa.Column("max_attempts", sa.Integer(), server_default="5"),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("outbox_events")
    op.drop_table("automation_assessments")
