"""Track Never Miss trial and cancellation lifecycle from Stripe webhooks."""

from alembic import op
import sqlalchemy as sa


revision = "20260820_nm_trial_lifecycle"
down_revision = "20260818_never_forget"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("product_subscriptions", sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("product_subscriptions", sa.Column("current_period_ends_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("product_subscriptions", sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column("product_subscriptions", "cancel_at_period_end")
    op.drop_column("product_subscriptions", "current_period_ends_at")
    op.drop_column("product_subscriptions", "trial_ends_at")
