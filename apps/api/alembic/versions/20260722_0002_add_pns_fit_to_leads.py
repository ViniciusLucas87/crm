"""add pns_fit_score and pns_fit_data to leads

Revision ID: 20260722_0002
Revises: 20260722_0001
Create Date: 2026-07-22
"""

from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "20260722_0002"
down_revision: str | None = "20260722_0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE leads ADD COLUMN IF NOT EXISTS pns_fit_score INTEGER")
    op.execute("ALTER TABLE leads ADD COLUMN IF NOT EXISTS pns_fit_data TEXT")


def downgrade() -> None:
    op.execute("ALTER TABLE leads DROP COLUMN IF EXISTS pns_fit_data")
    op.execute("ALTER TABLE leads DROP COLUMN IF EXISTS pns_fit_score")
