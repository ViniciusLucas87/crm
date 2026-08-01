"""add call pipeline columns

Revision ID: 20260722_0009
Revises: 20260722_0008
Create Date: 2026-07-22

Adds session_id, answered_at, provider_metadata, transcript_status, ai_status
to the calls table for the future AI conversation intelligence pipeline.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = "20260722_0009"
down_revision: Union[str, None] = "20260722_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("calls", sa.Column("session_id", sa.String(100), nullable=True))
    op.add_column("calls", sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("calls", sa.Column("provider_metadata", sa.Text(), nullable=True))
    op.add_column("calls", sa.Column("transcript_status", sa.String(20), nullable=False, server_default="none"))
    op.add_column("calls", sa.Column("ai_status", sa.String(20), nullable=False, server_default="none"))
    op.create_index("ix_calls_session_id", "calls", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_calls_session_id", table_name="calls")
    op.drop_column("calls", "ai_status")
    op.drop_column("calls", "transcript_status")
    op.drop_column("calls", "provider_metadata")
    op.drop_column("calls", "answered_at")
    op.drop_column("calls", "session_id")
