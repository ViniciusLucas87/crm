"""add product_recommendation_data to leads

Revision ID: 20260722_0005
Revises: 20260722_0004
Create Date: 2026-07-22
"""

from collections.abc import Sequence
from alembic import op

revision: str = "20260722_0005"
down_revision: str | None = "20260722_0004"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE leads ADD COLUMN IF NOT EXISTS product_recommendation_data TEXT")


def downgrade() -> None:
    op.execute("ALTER TABLE leads DROP COLUMN IF EXISTS product_recommendation_data")
