"""persistent call session upgrade (Sprint 48.1)

Revision ID: 20260801_0002
Revises: 20260801_0001
Create Date: 2026-08-01

Upgrades the existing calls table from the pre-48.1 partial schema to the
full persistent call lifecycle schema:
  - adds public_uuid, outcome, talk time, normalized phone numbers
  - adds lead_id, opportunity_id, owner_user_id
  - adds ringing_at, connected_at, disconnect_reason, failure fields
  - adds provider_leg_id, provider_session_id, correlation_id
  - adds post_call_status, timestamps
  - adds unique constraint on provider_call_id
  - converts metadata_json from Text to JSONB
  - drops old answered_at + ai_status columns
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260801_0002"
down_revision: Union[str, None] = "20260801_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns (nullable by default for existing rows)
    op.add_column("calls", sa.Column("public_uuid", sa.String(36), nullable=True))
    op.add_column("calls", sa.Column("lead_id", sa.Integer(), nullable=True))
    op.add_column("calls", sa.Column("opportunity_id", sa.Integer(), nullable=True))
    op.add_column("calls", sa.Column("owner_user_id", sa.String(255), nullable=True))
    op.add_column("calls", sa.Column("outcome", sa.String(20), nullable=True))
    op.add_column("calls", sa.Column("normalized_caller_number", sa.String(50), nullable=True))
    op.add_column("calls", sa.Column("normalized_destination_number", sa.String(50), nullable=True))
    op.add_column("calls", sa.Column("provider_leg_id", sa.String(255), nullable=True))
    op.add_column("calls", sa.Column("provider_session_id", sa.String(255), nullable=True))
    op.add_column("calls", sa.Column("correlation_id", sa.String(64), nullable=True))
    op.add_column("calls", sa.Column("ringing_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("calls", sa.Column("connected_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("calls", sa.Column("agent_talk_seconds", sa.Integer(), nullable=True))
    op.add_column("calls", sa.Column("prospect_talk_seconds", sa.Integer(), nullable=True))
    op.add_column("calls", sa.Column("silence_seconds", sa.Integer(), nullable=True))
    op.add_column("calls", sa.Column("disconnect_reason", sa.String(50), nullable=True))
    op.add_column("calls", sa.Column("failure_code", sa.String(20), nullable=True))
    op.add_column("calls", sa.Column("failure_message", sa.Text(), nullable=True))
    op.add_column("calls", sa.Column("post_call_status", sa.String(20), nullable=True, server_default="none"))
    op.add_column("calls", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()))

    # Convert metadata_json from Text to JSONB
    op.execute("ALTER TABLE calls ALTER COLUMN metadata_json TYPE JSONB USING metadata_json::jsonb")

    # Populate public_uuid for existing rows
    op.execute("UPDATE calls SET public_uuid = gen_random_uuid() WHERE public_uuid IS NULL")
    op.alter_column("calls", "public_uuid", nullable=False)

    # Add unique constraint on provider_call_id
    op.create_unique_constraint("uq_calls_provider_call_id", "calls", ["provider_call_id"])

    # Add indexes
    op.create_index("ix_calls_public_uuid", "calls", ["public_uuid"], unique=True)
    op.create_index("ix_calls_status", "calls", ["status"])
    op.create_index("ix_calls_provider_call_id", "calls", ["provider_call_id"])
    op.create_index("ix_calls_correlation_id", "calls", ["correlation_id"])
    op.create_index("ix_calls_lead_id", "calls", ["lead_id"])
    op.create_index("ix_calls_normalized_caller_number", "calls", ["normalized_caller_number"])
    op.create_index("ix_calls_normalized_destination_number", "calls", ["normalized_destination_number"])

    # Add foreign keys
    op.create_foreign_key("fk_calls_lead_id", "calls", "leads", ["lead_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_calls_opportunity_id", "calls", "opportunities", ["opportunity_id"], ["id"], ondelete="SET NULL")

    # Drop old columns
    op.drop_column("calls", "answered_at")
    op.drop_column("calls", "ai_status")


def downgrade() -> None:
    op.add_column("calls", sa.Column("ai_status", sa.String(20), nullable=True))
    op.add_column("calls", sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE calls SET answered_at = connected_at")

    op.drop_constraint("fk_calls_opportunity_id", "calls", type_="foreignkey")
    op.drop_constraint("fk_calls_lead_id", "calls", type_="foreignkey")
    op.drop_index("ix_calls_normalized_destination_number", table_name="calls")
    op.drop_index("ix_calls_normalized_caller_number", table_name="calls")
    op.drop_index("ix_calls_lead_id", table_name="calls")
    op.drop_index("ix_calls_correlation_id", table_name="calls")
    op.drop_index("ix_calls_provider_call_id", table_name="calls")
    op.drop_index("ix_calls_status", table_name="calls")
    op.drop_index("ix_calls_public_uuid", table_name="calls")
    op.drop_constraint("uq_calls_provider_call_id", "calls", type_="unique")

    op.drop_column("calls", "updated_at")
    op.drop_column("calls", "post_call_status")
    op.drop_column("calls", "failure_message")
    op.drop_column("calls", "failure_code")
    op.drop_column("calls", "disconnect_reason")
    op.drop_column("calls", "silence_seconds")
    op.drop_column("calls", "prospect_talk_seconds")
    op.drop_column("calls", "agent_talk_seconds")
    op.drop_column("calls", "connected_at")
    op.drop_column("calls", "ringing_at")
    op.drop_column("calls", "correlation_id")
    op.drop_column("calls", "provider_session_id")
    op.drop_column("calls", "provider_leg_id")
    op.drop_column("calls", "normalized_destination_number")
    op.drop_column("calls", "normalized_caller_number")
    op.drop_column("calls", "outcome")
    op.drop_column("calls", "owner_user_id")
    op.drop_column("calls", "opportunity_id")
    op.drop_column("calls", "lead_id")
    op.drop_column("calls", "public_uuid")
