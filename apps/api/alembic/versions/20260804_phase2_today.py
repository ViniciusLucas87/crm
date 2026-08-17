"""Phase 2: Today workspace — lead_id, owner_user_id, follow_up_actions

Revision ID: 20260804_phase2_today
Revises: 20260803_phase1_worker_hardening
Create Date: 2026-08-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260804_phase2_today"
down_revision: Union[str, None] = "20260803_phase1_worker_hardening"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Some long-lived local environments received the first task column before
    # this migration was recorded. Keep the upgrade safe for both those
    # databases and clean installs.
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    task_columns = {column["name"] for column in inspector.get_columns("tasks")}
    task_indexes = {index["name"] for index in inspector.get_indexes("tasks")}
    task_foreign_keys = inspector.get_foreign_keys("tasks")

    if "lead_id" not in task_columns:
        op.add_column("tasks", sa.Column("lead_id", sa.Integer(), nullable=True))
    if not any(fk.get("constrained_columns") == ["lead_id"] for fk in task_foreign_keys):
        op.create_foreign_key("fk_tasks_lead_id", "tasks", "leads", ["lead_id"], ["id"], ondelete="SET NULL")
    if "ix_tasks_lead_id" not in task_indexes:
        op.create_index("ix_tasks_lead_id", "tasks", ["lead_id"])
    if "owner_user_id" not in task_columns:
        op.add_column("tasks", sa.Column("owner_user_id", sa.String(255), nullable=True))

    lead_columns = {column["name"] for column in inspector.get_columns("leads")}
    lead_indexes = {index["name"] for index in inspector.get_indexes("leads")}
    if "owner_user_id" not in lead_columns:
        op.add_column("leads", sa.Column("owner_user_id", sa.String(255), nullable=True))
    if "ix_leads_owner_user_id" not in lead_indexes:
        op.create_index("ix_leads_owner_user_id", "leads", ["owner_user_id"])

    if not inspector.has_table("follow_up_actions"):
        op.create_table(
            "follow_up_actions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
            sa.Column("actor_user_id", sa.String(255), nullable=True),
            sa.Column("idempotency_key", sa.String(128), nullable=False),
            sa.Column("entity_type", sa.String(20), nullable=False),
            sa.Column("entity_id", sa.Integer(), nullable=False),
            sa.Column("action", sa.String(30), nullable=False),
            sa.Column("old_state", sa.Text(), nullable=True),
            sa.Column("new_state", sa.Text(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_follow_up_actions_org", "follow_up_actions", ["organization_id"])
        op.create_index("ix_follow_up_actions_entity", "follow_up_actions", ["entity_type", "entity_id"])
        op.create_unique_constraint("uq_follow_up_actions_idempotency_key", "follow_up_actions", ["idempotency_key"])


def downgrade() -> None:
    op.drop_table("follow_up_actions")
    op.drop_index("ix_leads_owner_user_id", table_name="leads")
    op.drop_column("leads", "owner_user_id")
    op.drop_column("tasks", "owner_user_id")
    op.drop_index("ix_tasks_lead_id", table_name="tasks")
    op.drop_constraint("fk_tasks_lead_id", "tasks", type_="foreignkey")
    op.drop_column("tasks", "lead_id")
