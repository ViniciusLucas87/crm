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
    op.add_column("tasks", sa.Column("lead_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_tasks_lead_id", "tasks", "leads", ["lead_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_tasks_lead_id", "tasks", ["lead_id"])
    op.add_column("tasks", sa.Column("owner_user_id", sa.String(255), nullable=True))
    op.add_column("leads", sa.Column("owner_user_id", sa.String(255), nullable=True))
    op.create_index("ix_leads_owner_user_id", "leads", ["owner_user_id"])
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
