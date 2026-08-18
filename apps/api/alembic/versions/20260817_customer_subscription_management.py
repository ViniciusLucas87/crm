"""Add secure customer subscription management tokens.

Revision ID: 20260817_customer_management
Revises: 20260817_token_channels
"""

from alembic import op
import sqlalchemy as sa


revision = "20260817_customer_management"
down_revision = "20260817_token_channels"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("product_subscriptions", sa.Column("management_token_hash", sa.String(64), nullable=True))
    op.add_column("product_subscriptions", sa.Column("management_token_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.create_unique_constraint("uq_product_subscriptions_management_token_hash", "product_subscriptions", ["management_token_hash"])


def downgrade() -> None:
    op.drop_constraint("uq_product_subscriptions_management_token_hash", "product_subscriptions", type_="unique")
    op.drop_column("product_subscriptions", "management_token_expires_at")
    op.drop_column("product_subscriptions", "management_token_hash")
