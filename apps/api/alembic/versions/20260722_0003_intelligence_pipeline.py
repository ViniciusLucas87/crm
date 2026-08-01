"""add enrichment_status to leads and create enrichment_jobs table

Revision ID: 20260722_0003
Revises: 20260722_0002
Create Date: 2026-07-22
"""

from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "20260722_0003"
down_revision: str | None = "20260722_0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE leads ADD COLUMN IF NOT EXISTS enrichment_status VARCHAR(20) DEFAULT 'pending' NOT NULL")
    op.execute("ALTER TABLE leads ADD COLUMN IF NOT EXISTS enrichment_job_id VARCHAR(100)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_leads_enrichment_status ON leads(enrichment_status)")

    op.create_table(
        "enrichment_jobs",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False, index=True),
        sa.Column("lead_id", sa.Integer(), nullable=False, index=True),
        sa.Column("discovery_source", sa.String(50), default="ai_discovery", nullable=False),
        sa.Column("priority", sa.Integer(), default=0, nullable=False),
        sa.Column("status", sa.String(20), default="queued", nullable=False, index=True),
        sa.Column("attempts", sa.Integer(), default=0, nullable=False),
        sa.Column("max_attempts", sa.Integer(), default=4, nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("worker_id", sa.String(100), nullable=True),
        sa.Column("processing_time_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("enrichment_jobs")
    op.execute("DROP INDEX IF EXISTS ix_leads_enrichment_status")
    op.execute("ALTER TABLE leads DROP COLUMN IF EXISTS enrichment_job_id")
    op.execute("ALTER TABLE leads DROP COLUMN IF EXISTS enrichment_status")
