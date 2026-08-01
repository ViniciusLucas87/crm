"""create calls table

Revision ID: 20260722_0008
Revises: 20260722_0007
Create Date: 2026-07-22
"""

from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "20260722_0008"
down_revision: str | None = "20260722_0007"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "calls",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("organization_id", sa.Integer(), nullable=False, index=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("contact_id", sa.Integer(), sa.ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("activity_id", sa.Integer(), sa.ForeignKey("activities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("provider", sa.String(50), nullable=False, default="telnyx"),
        sa.Column("provider_call_id", sa.String(255), nullable=True),
        sa.Column("direction", sa.String(20), nullable=False, default="outbound"),
        sa.Column("status", sa.String(20), nullable=False, default="idle"),
        sa.Column("phone_number", sa.String(50), nullable=False),
        sa.Column("caller_id", sa.String(50), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), default=0),
        sa.Column("recording_url", sa.String(1000), nullable=True),
        sa.Column("recording_status", sa.String(20), default="none"),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("calls")
