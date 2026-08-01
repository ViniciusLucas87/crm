"""worker runtime persistence

Revision ID: 20260723_worker_runtime
Revises: 20260723_demand_signals
Create Date: 2026-07-23
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260723_worker_runtime"
down_revision: str | None = "20260723_demand_signals"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "worker_schedules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("worker_name", sa.String(length=80), nullable=False),
        sa.Column("queue_name", sa.String(length=40), nullable=False, server_default="normal"),
        sa.Column("schedule_type", sa.String(length=30), nullable=False, server_default="event_triggered"),
        sa.Column("cron_expr", sa.String(length=120), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_enqueued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("worker_name"),
    )
    op.create_index("ix_worker_schedules_worker_name", "worker_schedules", ["worker_name"])

    op.create_table(
        "worker_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("worker_name", sa.String(length=80), nullable=False),
        sa.Column("task_id", sa.String(length=100), nullable=True),
        sa.Column("queue_name", sa.String(length=40), nullable=False, server_default="normal"),
        sa.Column("trigger_type", sa.String(length=30), nullable=False, server_default="event"),
        sa.Column("event_type", sa.String(length=80), nullable=True),
        sa.Column("entity_type", sa.String(length=80), nullable=True),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="queued"),
        sa.Column("priority", sa.String(length=20), nullable=False, server_default="normal"),
        sa.Column("retries", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("enqueued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_worker_jobs_worker_name", "worker_jobs", ["worker_name"])
    op.create_index("ix_worker_jobs_task_id", "worker_jobs", ["task_id"])
    op.create_index("ix_worker_jobs_status", "worker_jobs", ["status"])
    op.create_index("ix_worker_jobs_event_type", "worker_jobs", ["event_type"])
    op.create_index("ix_worker_jobs_entity_type", "worker_jobs", ["entity_type"])
    op.create_index("ix_worker_jobs_entity_id", "worker_jobs", ["entity_id"])

    op.create_table(
        "worker_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("worker_name", sa.String(length=80), nullable=False),
        sa.Column("task_id", sa.String(length=100), nullable=True),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("worker_jobs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="running"),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("runtime_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_worker_runs_worker_name", "worker_runs", ["worker_name"])
    op.create_index("ix_worker_runs_task_id", "worker_runs", ["task_id"])
    op.create_index("ix_worker_runs_job_id", "worker_runs", ["job_id"])
    op.create_index("ix_worker_runs_status", "worker_runs", ["status"])

    op.create_table(
        "worker_metric_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("worker_name", sa.String(length=80), nullable=False),
        sa.Column("queue_name", sa.String(length=40), nullable=False, server_default="normal"),
        sa.Column("current_job_id", sa.Integer(), sa.ForeignKey("worker_jobs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("jobs_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("jobs_succeeded", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("jobs_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("retries", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_runtime_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("facts_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("facts_verified", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("relationships_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("insights_generated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("entities_enriched", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("queue_depth", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_worker_metric_snapshots_worker_name", "worker_metric_snapshots", ["worker_name"])

    op.create_table(
        "worker_failures",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("worker_name", sa.String(length=80), nullable=False),
        sa.Column("task_id", sa.String(length=100), nullable=True),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("worker_jobs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("error_type", sa.String(length=120), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("traceback_text", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_worker_failures_worker_name", "worker_failures", ["worker_name"])
    op.create_index("ix_worker_failures_task_id", "worker_failures", ["task_id"])
    op.create_index("ix_worker_failures_job_id", "worker_failures", ["job_id"])
    op.create_index("ix_worker_failures_created_at", "worker_failures", ["created_at"])

    op.create_table(
        "worker_dead_letters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("worker_name", sa.String(length=80), nullable=False),
        sa.Column("task_id", sa.String(length=100), nullable=True),
        sa.Column("queue_name", sa.String(length=40), nullable=False, server_default="normal"),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="queued"),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("replayed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_worker_dead_letters_worker_name", "worker_dead_letters", ["worker_name"])
    op.create_index("ix_worker_dead_letters_task_id", "worker_dead_letters", ["task_id"])
    op.create_index("ix_worker_dead_letters_failed_at", "worker_dead_letters", ["failed_at"])


def downgrade() -> None:
    op.drop_index("ix_worker_dead_letters_failed_at", table_name="worker_dead_letters")
    op.drop_index("ix_worker_dead_letters_task_id", table_name="worker_dead_letters")
    op.drop_index("ix_worker_dead_letters_worker_name", table_name="worker_dead_letters")
    op.drop_table("worker_dead_letters")
    op.drop_index("ix_worker_failures_created_at", table_name="worker_failures")
    op.drop_index("ix_worker_failures_job_id", table_name="worker_failures")
    op.drop_index("ix_worker_failures_task_id", table_name="worker_failures")
    op.drop_index("ix_worker_failures_worker_name", table_name="worker_failures")
    op.drop_table("worker_failures")
    op.drop_index("ix_worker_metric_snapshots_worker_name", table_name="worker_metric_snapshots")
    op.drop_table("worker_metric_snapshots")
    op.drop_index("ix_worker_runs_status", table_name="worker_runs")
    op.drop_index("ix_worker_runs_job_id", table_name="worker_runs")
    op.drop_index("ix_worker_runs_task_id", table_name="worker_runs")
    op.drop_index("ix_worker_runs_worker_name", table_name="worker_runs")
    op.drop_table("worker_runs")
    op.drop_index("ix_worker_jobs_entity_id", table_name="worker_jobs")
    op.drop_index("ix_worker_jobs_entity_type", table_name="worker_jobs")
    op.drop_index("ix_worker_jobs_event_type", table_name="worker_jobs")
    op.drop_index("ix_worker_jobs_status", table_name="worker_jobs")
    op.drop_index("ix_worker_jobs_task_id", table_name="worker_jobs")
    op.drop_index("ix_worker_jobs_worker_name", table_name="worker_jobs")
    op.drop_table("worker_jobs")
    op.drop_index("ix_worker_schedules_worker_name", table_name="worker_schedules")
    op.drop_table("worker_schedules")