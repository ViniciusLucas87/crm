"""add assessment intelligence fields

Revision ID: 20260801_0001
Revises: 20260723_worker_runtime
Create Date: 2026-08-01

Adds structured intelligence columns to automation_assessments:
  - primary_pain_point, secondary_pain_points
  - current_process_summary, root_cause, business_impact
  - recommended_solution_categories, recommendation_reasons (JSONB)
  - urgency, buying_signals, likely_decision_maker
  - project_size_band, next_best_action
  - discovery_questions (JSONB)
  - intelligence_json (JSONB) — full structured intelligence
  - intelligence_version, intelligence_generated_at, intelligence_confidence
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260801_0001"
down_revision: Union[str, None] = "20260731_assessment_outbox"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("automation_assessments", sa.Column("primary_pain_point", sa.String(255), nullable=True))
    op.add_column("automation_assessments", sa.Column("secondary_pain_points", postgresql.JSONB, nullable=True))
    op.add_column("automation_assessments", sa.Column("current_process_summary", sa.Text, nullable=True))
    op.add_column("automation_assessments", sa.Column("root_cause", sa.Text, nullable=True))
    op.add_column("automation_assessments", sa.Column("business_impact", sa.Text, nullable=True))
    op.add_column("automation_assessments", sa.Column("recommended_solution_categories", postgresql.JSONB, nullable=True))
    op.add_column("automation_assessments", sa.Column("recommendation_reasons", postgresql.JSONB, nullable=True))
    op.add_column("automation_assessments", sa.Column("urgency", sa.String(20), nullable=True))
    op.add_column("automation_assessments", sa.Column("buying_signals", postgresql.JSONB, nullable=True))
    op.add_column("automation_assessments", sa.Column("likely_decision_maker", sa.String(255), nullable=True))
    op.add_column("automation_assessments", sa.Column("project_size_band", sa.String(20), nullable=True))
    op.add_column("automation_assessments", sa.Column("next_best_action", sa.Text, nullable=True))
    op.add_column("automation_assessments", sa.Column("discovery_questions", postgresql.JSONB, nullable=True))
    op.add_column("automation_assessments", sa.Column("intelligence_json", postgresql.JSONB, nullable=True))
    op.add_column("automation_assessments", sa.Column("intelligence_version", sa.String(20), nullable=True))
    op.add_column("automation_assessments", sa.Column("intelligence_generated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("automation_assessments", sa.Column("intelligence_confidence", sa.Numeric(4, 3), nullable=True))


def downgrade() -> None:
    op.drop_column("automation_assessments", "intelligence_confidence")
    op.drop_column("automation_assessments", "intelligence_generated_at")
    op.drop_column("automation_assessments", "intelligence_version")
    op.drop_column("automation_assessments", "intelligence_json")
    op.drop_column("automation_assessments", "discovery_questions")
    op.drop_column("automation_assessments", "next_best_action")
    op.drop_column("automation_assessments", "project_size_band")
    op.drop_column("automation_assessments", "likely_decision_maker")
    op.drop_column("automation_assessments", "buying_signals")
    op.drop_column("automation_assessments", "urgency")
    op.drop_column("automation_assessments", "recommendation_reasons")
    op.drop_column("automation_assessments", "recommended_solution_categories")
    op.drop_column("automation_assessments", "business_impact")
    op.drop_column("automation_assessments", "root_cause")
    op.drop_column("automation_assessments", "current_process_summary")
    op.drop_column("automation_assessments", "secondary_pain_points")
    op.drop_column("automation_assessments", "primary_pain_point")
