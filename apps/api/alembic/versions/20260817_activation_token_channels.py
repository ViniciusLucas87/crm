"""Keep email and checkout activation credentials independent."""

from alembic import op
import sqlalchemy as sa

revision: str = "20260817_token_channels"
down_revision: str | None = "20260817_self_service"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("product_subscriptions", sa.Column("redirect_token_hash", sa.String(length=64), nullable=True))
    op.add_column("product_subscriptions", sa.Column("redirect_token_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.create_unique_constraint("uq_product_subscriptions_redirect_token_hash", "product_subscriptions", ["redirect_token_hash"])


def downgrade() -> None:
    op.drop_constraint("uq_product_subscriptions_redirect_token_hash", "product_subscriptions", type_="unique")
    op.drop_column("product_subscriptions", "redirect_token_expires_at")
    op.drop_column("product_subscriptions", "redirect_token_hash")
