"""add google_maps_data to leads

Revision ID: 20260722_0004
Revises: 20260722_0003
Create Date: 2026-07-22
"""

from collections.abc import Sequence
from alembic import op

revision: str = "20260722_0004"
down_revision: str | None = "20260722_0003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE leads ADD COLUMN IF NOT EXISTS google_maps_data TEXT")


def downgrade() -> None:
    op.execute("ALTER TABLE leads DROP COLUMN IF EXISTS google_maps_data")
