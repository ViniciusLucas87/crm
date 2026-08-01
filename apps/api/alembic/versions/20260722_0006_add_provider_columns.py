"""add website_data, reviews_data, linkedin_data to leads

Revision ID: 20260722_0006
Revises: 20260722_0005
Create Date: 2026-07-22
"""

from collections.abc import Sequence
from alembic import op

revision: str = "20260722_0006"
down_revision: str | None = "20260722_0005"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE leads ADD COLUMN IF NOT EXISTS website_data TEXT")
    op.execute("ALTER TABLE leads ADD COLUMN IF NOT EXISTS reviews_data TEXT")
    op.execute("ALTER TABLE leads ADD COLUMN IF NOT EXISTS linkedin_data TEXT")


def downgrade() -> None:
    op.execute("ALTER TABLE leads DROP COLUMN IF EXISTS linkedin_data")
    op.execute("ALTER TABLE leads DROP COLUMN IF EXISTS reviews_data")
    op.execute("ALTER TABLE leads DROP COLUMN IF EXISTS website_data")
