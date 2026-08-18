"""Add Never Forget controlled MVP tables.

Revision ID: 20260818_never_forget
Revises: 20260818_app_factory
"""

import sqlalchemy as sa
from alembic import op

revision = "20260818_never_forget"
down_revision = "20260818_app_factory"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "UPDATE app_factory_candidates SET decision = 'controlled_mvp', "
        "decision_reason = 'Owner selected a controlled MVP. Live communications and public release remain gated.' "
        "WHERE slug = 'never-forget'"
    )
    op.create_table("never_forget_service_records",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("public_token_hash", sa.String(64), nullable=False), sa.Column("contractor_name", sa.String(255), nullable=False),
        sa.Column("contractor_phone", sa.String(50)), sa.Column("contractor_email", sa.String(255)),
        sa.Column("customer_name", sa.String(255), nullable=False), sa.Column("customer_phone", sa.String(50)), sa.Column("customer_email", sa.String(255)),
        sa.Column("service_address", sa.String(500)), sa.Column("job_title", sa.String(255), nullable=False), sa.Column("job_summary", sa.Text(), nullable=False),
        sa.Column("completed_on", sa.Date(), nullable=False), sa.Column("invoice_reference", sa.String(120)), sa.Column("receipt_url", sa.String(1200)),
        sa.Column("work_photo_urls_json", sa.Text(), nullable=False, server_default="[]"), sa.Column("warranty_summary", sa.Text()), sa.Column("warranty_expires_on", sa.Date()),
        sa.Column("maintenance_instructions", sa.Text()), sa.Column("next_service_on", sa.Date()), sa.Column("customer_consented_to_reminders", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"), sa.Column("created_by", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "public_token_hash", name="uq_never_forget_org_token"), sa.UniqueConstraint("public_token_hash"),
    )
    op.create_index("ix_never_forget_record_org", "never_forget_service_records", ["organization_id", "status"])
    op.create_index("ix_never_forget_record_next_service", "never_forget_service_records", ["next_service_on"])
    op.create_table("never_forget_reminders",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("service_record_id", sa.Integer(), sa.ForeignKey("never_forget_service_records.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reminder_type", sa.String(40), nullable=False), sa.Column("channel", sa.String(20), nullable=False, server_default="sms"),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False), sa.Column("status", sa.String(30), nullable=False, server_default="scheduled"),
        sa.Column("message", sa.Text(), nullable=False), sa.Column("sent_at", sa.DateTime(timezone=True)), sa.Column("provider_message_id", sa.String(255)), sa.Column("last_error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("service_record_id", "reminder_type", "scheduled_for", name="uq_never_forget_reminder_schedule"),
    )
    op.create_index("ix_never_forget_reminder_due", "never_forget_reminders", ["organization_id", "status", "scheduled_for"])
    op.create_table("never_forget_customer_actions",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("service_record_id", sa.Integer(), sa.ForeignKey("never_forget_service_records.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action_type", sa.String(40), nullable=False), sa.Column("note", sa.Text()), sa.Column("status", sa.String(30), nullable=False, server_default="new"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_never_forget_action_queue", "never_forget_customer_actions", ["organization_id", "status", "created_at"])


def downgrade() -> None:
    op.execute(
        "UPDATE app_factory_candidates SET decision = 'research', "
        "decision_reason = 'Returned to research after controlled MVP rollback.' "
        "WHERE slug = 'never-forget'"
    )
    op.drop_table("never_forget_customer_actions")
    op.drop_table("never_forget_reminders")
    op.drop_table("never_forget_service_records")
