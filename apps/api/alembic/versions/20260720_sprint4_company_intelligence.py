"""sprint4_company_intelligence

Revision ID: sprint4_001
Revises: sprint3_001
Create Date: 2026-07-20

- Add company intelligence fields (description, locations, founded, social URLs, opportunity_score, confidence_score, buying_signals, research_status, research_date, source_history)
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "sprint4_001"
down_revision: Union[str, None] = "sprint3_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("companies", sa.Column("locations", sa.Text(), nullable=True))
    op.add_column("companies", sa.Column("founded", sa.Integer(), nullable=True))
    op.add_column("companies", sa.Column("linkedin_url", sa.String(500), nullable=True))
    op.add_column("companies", sa.Column("facebook_url", sa.String(500), nullable=True))
    op.add_column("companies", sa.Column("instagram_url", sa.String(500), nullable=True))
    op.add_column("companies", sa.Column("twitter_url", sa.String(500), nullable=True))
    op.add_column("companies", sa.Column("youtube_url", sa.String(500), nullable=True))
    op.add_column("companies", sa.Column("google_business", sa.String(500), nullable=True))
    op.add_column("companies", sa.Column("business_categories", sa.Text(), nullable=True))
    op.add_column("companies", sa.Column("opportunity_score", sa.Integer(), nullable=True))
    op.add_column("companies", sa.Column("confidence_score", sa.Integer(), nullable=True))
    op.add_column("companies", sa.Column("buying_signals", sa.Text(), nullable=True))
    op.add_column("companies", sa.Column("research_status", sa.String(30), server_default="pending", nullable=False))
    op.add_column("companies", sa.Column("research_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("companies", sa.Column("source_history", sa.Text(), nullable=True))
    op.add_column("companies", sa.Column("city", sa.String(120), nullable=True))
    op.add_column("companies", sa.Column("province", sa.String(120), nullable=True))
    op.add_column("companies", sa.Column("country", sa.String(120), nullable=True))
    op.add_column("companies", sa.Column("business_type", sa.String(120), nullable=True))
    op.create_index("ix_companies_research_status", "companies", ["research_status"])


def downgrade() -> None:
    op.drop_index("ix_companies_research_status")
    for col in ["business_type", "country", "province", "city", "source_history", "research_date", "research_status", "buying_signals", "confidence_score", "opportunity_score", "business_categories", "google_business", "youtube_url", "twitter_url", "instagram_url", "facebook_url", "linkedin_url", "founded", "locations", "description"]:
        op.drop_column("companies", col)
