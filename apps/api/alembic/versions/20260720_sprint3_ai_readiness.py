"""ai_readiness

Revision ID: sprint3_001
Revises: sprint2_001
Create Date: 2026-07-20

- Add AI metadata columns to companies
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "sprint3_001"
down_revision: Union[str, None] = "sprint2_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("ai_summary", sa.Text(), nullable=True))
    op.add_column("companies", sa.Column("last_ai_update", sa.DateTime(timezone=True), nullable=True))
    op.add_column("companies", sa.Column("embedding_ref", sa.String(255), nullable=True))
    op.add_column("companies", sa.Column("tech_stack", sa.Text(), nullable=True))
    op.add_column("companies", sa.Column("social_links", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("companies", "social_links")
    op.drop_column("companies", "tech_stack")
    op.drop_column("companies", "embedding_ref")
    op.drop_column("companies", "last_ai_update")
    op.drop_column("companies", "ai_summary")
