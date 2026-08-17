"""Self-service subscription activation

Revision ID: 20260817_self_service
Revises: 20260817_products_mvp
"""

from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "20260817_self_service"
down_revision: str | None = "20260817_never_miss_brand"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "product_subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("stripe_checkout_session_id", sa.String(255), nullable=False, unique=True),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True, unique=True),
        sa.Column("stripe_payment_link_id", sa.String(255), nullable=False),
        sa.Column("plan", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="paid"),
        sa.Column("customer_email", sa.String(255), nullable=False),
        sa.Column("customer_name", sa.String(255), nullable=True),
        sa.Column("business_name", sa.String(255), nullable=True),
        sa.Column("existing_phone", sa.String(50), nullable=True),
        sa.Column("notification_phone", sa.String(50), nullable=True),
        sa.Column("assigned_phone", sa.String(50), nullable=True, unique=True),
        sa.Column("telnyx_number_order_id", sa.String(255), nullable=True),
        sa.Column("onboarding_token_hash", sa.String(64), nullable=True, unique=True),
        sa.Column("onboarding_token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("onboarding_data_json", sa.JSON(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    for column in ("organization_id", "stripe_checkout_session_id", "stripe_customer_id", "stripe_subscription_id", "stripe_payment_link_id", "status", "customer_email"):
        op.create_index(f"ix_product_subscriptions_{column}", "product_subscriptions", [column])

    op.create_table(
        "stripe_webhook_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("stripe_event_id", sa.String(255), nullable=False, unique=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("livemode", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_stripe_webhook_events_stripe_event_id", "stripe_webhook_events", ["stripe_event_id"])
    op.create_index("ix_stripe_webhook_events_event_type", "stripe_webhook_events", ["event_type"])


def downgrade() -> None:
    op.drop_table("stripe_webhook_events")
    op.drop_table("product_subscriptions")
