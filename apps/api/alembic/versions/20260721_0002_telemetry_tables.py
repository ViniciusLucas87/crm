"""telemetry tables

Revision ID: 20260721_0002
Revises: 20260721_0001
Create Date: 2026-07-21
"""

from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "20260721_0002"
down_revision: str | None = "20260721_0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table("ai_request_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.String(64), nullable=False),
        sa.Column("feature", sa.String(50), nullable=False),
        sa.Column("provider", sa.String(30), nullable=False),
        sa.Column("model", sa.String(50), nullable=False),
        sa.Column("prompt_name", sa.String(50), nullable=True),
        sa.Column("input_tokens", sa.Integer(), default=0),
        sa.Column("output_tokens", sa.Integer(), default=0),
        sa.Column("total_tokens", sa.Integer(), default=0),
        sa.Column("estimated_cost", sa.Numeric(10, 6), default=0),
        sa.Column("latency_ms", sa.Integer(), default=0),
        sa.Column("success", sa.Boolean(), default=True),
        sa.Column("fallback_used", sa.Boolean(), default=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("parse_success", sa.Boolean(), nullable=True),
        sa.Column("parse_method", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_request_logs_org", "ai_request_logs", ["organization_id"])
    op.create_index("ix_ai_request_logs_feature", "ai_request_logs", ["feature"])
    op.create_index("ix_ai_request_logs_created", "ai_request_logs", ["created_at"])

    op.create_table("mcp_tool_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("tool_name", sa.String(50), nullable=False),
        sa.Column("arguments", sa.Text(), nullable=True),
        sa.Column("execution_time_ms", sa.Integer(), default=0),
        sa.Column("success", sa.Boolean(), default=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mcp_tool_logs_org", "mcp_tool_logs", ["organization_id"])
    op.create_index("ix_mcp_tool_logs_tool", "mcp_tool_logs", ["tool_name"])
    op.create_index("ix_mcp_tool_logs_created", "mcp_tool_logs", ["created_at"])

    op.create_table("daily_metrics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("total_requests", sa.Integer(), default=0),
        sa.Column("total_tokens", sa.Integer(), default=0),
        sa.Column("total_cost", sa.Numeric(10, 6), default=0),
        sa.Column("avg_latency_ms", sa.Integer(), default=0),
        sa.Column("success_rate", sa.Numeric(5, 2), default=100),
        sa.Column("fallback_rate", sa.Numeric(5, 2), default=0),
        sa.Column("companies_analyzed", sa.Integer(), default=0),
        sa.Column("proposals_generated", sa.Integer(), default=0),
        sa.Column("health_score", sa.Integer(), default=100),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_daily_metrics_org_date", "daily_metrics", ["organization_id", "metric_date"])


def downgrade() -> None:
    op.drop_table("daily_metrics")
    op.drop_table("mcp_tool_logs")
    op.drop_table("ai_request_logs")
