"""Persist delivery receipts for manually sent CRM text messages.

Revision ID: 20260821_manual_sms_delivery
Revises: 20260820_nm_trial_lifecycle
"""

import sqlalchemy as sa

from alembic import op

revision = "20260821_manual_sms_delivery"
down_revision = "20260820_nm_trial_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("activities", sa.Column("provider_message_id", sa.String(255), nullable=True))
    op.add_column("activities", sa.Column("delivery_status", sa.String(30), nullable=True))
    op.create_index("ix_activities_provider_message_id", "activities", ["provider_message_id"], unique=True)
    op.create_index("ix_activities_delivery_status", "activities", ["delivery_status"])


def downgrade() -> None:
    op.drop_index("ix_activities_delivery_status", table_name="activities")
    op.drop_index("ix_activities_provider_message_id", table_name="activities")
    op.drop_column("activities", "delivery_status")
    op.drop_column("activities", "provider_message_id")
