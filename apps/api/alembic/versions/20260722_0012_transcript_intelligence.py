"""transcript storage and conversation intelligence

Revision ID: 20260722_0012
Revises: 20260722_0011
Create Date: 2026-07-23

Adds transcript, transcript_segment, and conversation_insight tables.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260722_0012"
down_revision: Union[str, None] = "20260722_0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "transcripts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("call_id", sa.Integer(), nullable=True),
        sa.Column("conversation_id", sa.Integer(), nullable=True),
        sa.Column("provider", sa.String(50), nullable=False, server_default="deepgram"),
        sa.Column("status", sa.String(20), nullable=False, server_default="in_progress"),
        sa.Column("language", sa.String(10), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["call_id"], ["calls.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_transcripts_id", "transcripts", ["id"])
    op.create_index("ix_transcripts_call", "transcripts", ["call_id"])

    op.create_table(
        "transcript_segments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("transcript_id", sa.Integer(), nullable=False),
        sa.Column("speaker", sa.String(50), nullable=False, server_default="Speaker 0"),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("start_time", sa.Numeric(10, 3), default=0.0),
        sa.Column("end_time", sa.Numeric(10, 3), default=0.0),
        sa.Column("confidence", sa.Numeric(5, 3), default=0.0),
        sa.Column("is_final", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sequence", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["transcript_id"], ["transcripts.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_transcript_segments_id", "transcript_segments", ["id"])
    op.create_index("ix_transcript_segments_tid", "transcript_segments", ["transcript_id"])

    op.create_table(
        "conversation_insights",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("transcript_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=True),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Integer(), default=50),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column("speaker", sa.String(50), nullable=True),
        sa.Column("segment_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["transcript_id"], ["transcripts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_conversation_insights_id", "conversation_insights", ["id"])
    op.create_index("ix_conversation_insights_cat", "conversation_insights", ["category"])
    op.create_index("ix_conversation_insights_tid", "conversation_insights", ["transcript_id"])


def downgrade() -> None:
    op.drop_table("conversation_insights")
    op.drop_table("transcript_segments")
    op.drop_table("transcripts")
