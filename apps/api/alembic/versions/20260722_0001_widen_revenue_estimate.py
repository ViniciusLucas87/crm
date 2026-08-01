"""widen revenue_estimate column

Revision ID: 20260722_0001
Revises: 20260721_0004
Create Date: 2026-07-22
"""

from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "20260722_0001"
down_revision: str | None = "20260721_0004"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("leads", "revenue_estimate", type_=sa.Text(), existing_type=sa.String(50))


def downgrade() -> None:
    op.alter_column("leads", "revenue_estimate", type_=sa.String(50), existing_type=sa.Text())
