"""add missing columns to tasks and activities

Revision ID: 20260721_0001
Revises: 20260720_sprint4_company_intelligence
Create Date: 2026-07-21 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260721_0001"
down_revision: str | None = "sprint4_001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # Add created_at to tasks if missing
    op.execute("""
        ALTER TABLE tasks ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
    """)

    # Add contact_id to activities if missing
    op.execute("""
        ALTER TABLE activities ADD COLUMN IF NOT EXISTS contact_id INTEGER REFERENCES contacts(id) ON DELETE SET NULL
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE tasks DROP COLUMN IF EXISTS created_at")
    op.execute("ALTER TABLE activities DROP COLUMN IF EXISTS contact_id")
