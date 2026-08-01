"""add email_messages table (Sprint 48.2)

Revision ID: 20260801_0003
Revises: 20260801_0002
Create Date: 2026-08-01

Creates the email_messages table for outbound/inbound email logging,
threading, and entity resolution.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260801_0003"
down_revision: Union[str, None] = "20260801_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "email_messages",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("public_uuid", sa.String(36), nullable=False, unique=True, index=True),
        sa.Column("organization_id", sa.Integer(), nullable=False, index=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("contact_id", sa.Integer(), sa.ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("lead_id", sa.Integer(), sa.ForeignKey("leads.id", ondelete="SET NULL"), nullable=True),
        sa.Column("opportunity_id", sa.Integer(), sa.ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("activity_id", sa.Integer(), sa.ForeignKey("activities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("owner_user_id", sa.String(255), nullable=True),
        sa.Column("provider_message_id", sa.String(500), nullable=True, unique=True, index=True),
        sa.Column("provider_thread_id", sa.String(500), nullable=True, index=True),
        sa.Column("internet_message_id", sa.String(500), nullable=True, index=True),
        sa.Column("in_reply_to", sa.String(500), nullable=True),
        sa.Column("references", sa.Text(), nullable=True),
        sa.Column("thread_id", sa.Integer(), sa.ForeignKey("email_messages.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("direction", sa.String(20), nullable=False, server_default="outbound"),
        sa.Column("channel", sa.String(20), nullable=False, server_default="email"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending", index=True),
        sa.Column("delivery_status", sa.String(20), nullable=True),
        sa.Column("from_address", sa.String(255), nullable=False, index=True),
        sa.Column("normalized_from", sa.String(255), nullable=True, index=True),
        sa.Column("to_address", sa.Text(), nullable=True),
        sa.Column("cc_address", sa.Text(), nullable=True),
        sa.Column("bcc_address", sa.Text(), nullable=True),
        sa.Column("subject", sa.String(500), nullable=True),
        sa.Column("plain_text", sa.Text(), nullable=True),
        sa.Column("html_reference", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provider", sa.String(50), nullable=False, server_default="zoho"),
        sa.Column("correlation_id", sa.String(64), nullable=True, index=True),
        sa.Column("provider_metadata", postgresql.JSONB, nullable=True),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_email_messages_direction", "email_messages", ["direction"])


def downgrade() -> None:
    op.drop_table("email_messages")
