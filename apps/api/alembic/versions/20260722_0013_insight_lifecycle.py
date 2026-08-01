"""insight lifecycle and deduplication

Revision ID: 20260722_0013
Revises: 20260722_0012
Create Date: 2026-07-23

Adds status, source, created_by, verified_by, verified_at, resolved_at,
metadata_json to conversation_insights for lifecycle management.
Adds dedup index on (conversation_id, category, value).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260722_0013"
down_revision: Union[str, None] = "20260722_0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("conversation_insights", sa.Column("status", sa.String(20), nullable=False, server_default="detected"))
    op.add_column("conversation_insights", sa.Column("source", sa.String(20), nullable=False, server_default="transcript"))
    op.add_column("conversation_insights", sa.Column("created_by", sa.String(20), nullable=False, server_default="ai"))
    op.add_column("conversation_insights", sa.Column("verified_by", sa.String(255), nullable=True))
    op.add_column("conversation_insights", sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("conversation_insights", sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("conversation_insights", sa.Column("metadata_json", sa.Text(), nullable=True))
    op.create_index("ix_insights_status", "conversation_insights", ["status"])
    op.create_index("ix_insights_dedup", "conversation_insights", ["conversation_id", "category", "value"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_insights_dedup", table_name="conversation_insights")
    op.drop_index("ix_insights_status", table_name="conversation_insights")
    op.drop_column("conversation_insights", "metadata_json")
    op.drop_column("conversation_insights", "resolved_at")
    op.drop_column("conversation_insights", "verified_at")
    op.drop_column("conversation_insights", "verified_by")
    op.drop_column("conversation_insights", "created_by")
    op.drop_column("conversation_insights", "source")
    op.drop_column("conversation_insights", "status")
