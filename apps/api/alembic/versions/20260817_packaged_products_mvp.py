"""Never Miss product configuration and customer inquiry storage

Revision ID: 20260817_products_mvp
Revises: 20260804_phase2_today
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260817_products_mvp"
down_revision: str | None = "20260804_phase2_today"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "product_configurations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_code", sa.String(50), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("plan", sa.String(30), nullable=False, server_default="pilot"),
        sa.Column("business_name", sa.String(255), nullable=True),
        sa.Column("business_phone", sa.String(50), nullable=True),
        sa.Column("notification_phone", sa.String(50), nullable=True),
        sa.Column("recovery_message", sa.Text(), nullable=True),
        sa.Column("business_hours_json", sa.JSON(), nullable=True),
        sa.Column("monthly_call_limit", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("monthly_message_limit", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("intake_key_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("organization_id", "product_code", name="uq_product_config_org_code"),
        sa.UniqueConstraint("intake_key_hash", name="uq_product_config_intake_key_hash"),
    )
    op.create_index("ix_product_config_org", "product_configurations", ["organization_id"])
    op.create_index("ix_product_config_code", "product_configurations", ["product_code"])

    op.create_table(
        "lead_capture_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source", sa.String(40), nullable=False),
        sa.Column("external_id", sa.String(128), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="new"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="normal"),
        sa.Column("owner_user_id", sa.String(255), nullable=True),
        sa.Column("next_action", sa.String(255), nullable=True),
        sa.Column("next_action_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("organization_id", "source", "external_id", name="uq_lead_capture_source_external"),
    )
    op.create_index("ix_lead_capture_org", "lead_capture_records", ["organization_id"])
    op.create_index("ix_lead_capture_source", "lead_capture_records", ["source"])
    op.create_index("ix_lead_capture_status", "lead_capture_records", ["status"])
    op.create_index("ix_lead_capture_created", "lead_capture_records", ["created_at"])


def downgrade() -> None:
    op.drop_table("lead_capture_records")
    op.drop_table("product_configurations")
