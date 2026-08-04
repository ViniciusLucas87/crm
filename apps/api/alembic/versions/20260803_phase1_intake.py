"""Phase 1: Lead Intake and Missed Contact Recovery

Revision ID: 20260803_phase1_intake
Revises: 20260801_0003
Create Date: 2026-08-03

Adds:
- provider_webhook_events table (immutable event ledger, unique on provider event id)
- phone_suppressions table (STOP/START opt-out)
- spam_score, spam_reasons, sms_status, sms_sent_at, sms_message_id to calls
- idempotency_key to calls for task/activity/SMS deduplication
- call_leg_id and normalized_caller_number indexes
- source and sla_deadline columns on tasks
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260803_phase1_intake"
down_revision: Union[str, None] = "20260801_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Provider webhook event ledger (immutable, unique on provider event id)
    op.create_table(
        "provider_webhook_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("provider_event_id", sa.String(255), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False, server_default="telnyx"),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("call_control_id", sa.String(255), nullable=True),
        sa.Column("call_leg_id", sa.String(255), nullable=True),
        sa.Column("payload_hash", sa.String(64), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("processing_status", sa.String(20), nullable=False, server_default="received"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint(
        "uq_webhook_events_provider_event_id",
        "provider_webhook_events",
        ["provider_event_id"],
    )
    op.create_index("ix_webhook_events_call_control", "provider_webhook_events", ["call_control_id"])
    op.create_index("ix_webhook_events_call_leg", "provider_webhook_events", ["call_leg_id"])
    op.create_index("ix_webhook_events_status", "provider_webhook_events", ["processing_status"])

    # Calls table additions
    op.add_column("calls", sa.Column("spam_score", sa.Integer(), nullable=True))
    op.add_column("calls", sa.Column("spam_reasons", sa.Text(), nullable=True))
    op.add_column("calls", sa.Column("idempotency_key", sa.String(128), nullable=True))
    op.create_unique_constraint("uq_calls_idempotency_key", "calls", ["idempotency_key"])
    op.create_index("ix_calls_provider_leg_id", "calls", ["provider_leg_id"])
    op.create_index("ix_calls_normalized_caller", "calls", ["normalized_caller_number"])

    # SMS send tracking on calls
    op.add_column("calls", sa.Column("sms_status", sa.String(20), nullable=True))
    op.add_column("calls", sa.Column("sms_sent_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("calls", sa.Column("sms_message_id", sa.String(255), nullable=True))

    # Phone suppressions table (STOP/START)
    op.create_table(
        "phone_suppressions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("phone_number", sa.String(50), nullable=False),
        sa.Column("normalized_phone", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="suppressed"),
        sa.Column("reason", sa.String(50), nullable=True),
        sa.Column("source_event_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint(
        "uq_phone_suppressions_org_phone",
        "phone_suppressions",
        ["organization_id", "normalized_phone"],
    )
    op.create_index("ix_phone_suppressions_status", "phone_suppressions", ["status"])

    # Tasks: source and sla_deadline
    op.add_column("tasks", sa.Column("source", sa.String(50), nullable=True))
    op.add_column("tasks", sa.Column("sla_deadline", sa.DateTime(timezone=True), nullable=True))

    # Activity: company_id nullable for unknown-caller missed calls
    op.alter_column("activities", "company_id", existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    # Activity: revert company_id to NOT NULL only if safe
    conn = op.get_bind()
    null_count = conn.execute(
        sa.text("SELECT COUNT(*) FROM activities WHERE company_id IS NULL")
    ).scalar()
    if null_count > 0:
        raise RuntimeError(
            f"Cannot downgrade: {null_count} activities have NULL company_id. "
            "Set company_id on those rows before downgrading."
        )
    op.alter_column("activities", "company_id", existing_type=sa.Integer(), nullable=False)

    op.drop_column("tasks", "sla_deadline")
    op.drop_column("tasks", "source")

    op.drop_index("ix_phone_suppressions_status", table_name="phone_suppressions")
    op.drop_constraint("uq_phone_suppressions_org_phone", "phone_suppressions", type_="unique")
    op.drop_table("phone_suppressions")

    op.drop_column("calls", "sms_message_id")
    op.drop_column("calls", "sms_sent_at")
    op.drop_column("calls", "sms_status")

    op.drop_index("ix_calls_normalized_caller", table_name="calls")
    op.drop_index("ix_calls_provider_leg_id", table_name="calls")
    op.drop_constraint("uq_calls_idempotency_key", "calls", type_="unique")
    op.drop_column("calls", "idempotency_key")
    op.drop_column("calls", "spam_reasons")
    op.drop_column("calls", "spam_score")

    op.drop_index("ix_webhook_events_status", table_name="provider_webhook_events")
    op.drop_index("ix_webhook_events_call_leg", table_name="provider_webhook_events")
    op.drop_index("ix_webhook_events_call_control", table_name="provider_webhook_events")
    op.drop_constraint("uq_webhook_events_provider_event_id", "provider_webhook_events", type_="unique")
    op.drop_table("provider_webhook_events")
