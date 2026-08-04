"""Phase 1 worker hardening: idempotency, row locking, recovery keys.

Revision ID: 20260803_phase1_worker_hardening
Revises: 20260803_phase1_intake
Create Date: 2026-08-03

Adds:
- idempotency_key (unique) to outbox_events for concurrency-safe dedup
- leased_at, lease_holder to outbox_events for SELECT FOR UPDATE SKIP LOCKED
- recovery_key (unique, nullable) to tasks for missed-call recovery dedup
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260803_phase1_worker_hardening"
down_revision: Union[str, None] = "20260803_phase1_intake"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("outbox_events", sa.Column("idempotency_key", sa.String(128), nullable=True))
    op.create_unique_constraint("uq_outbox_events_idempotency_key", "outbox_events", ["idempotency_key"])
    op.create_index("ix_outbox_events_idempotency_key", "outbox_events", ["idempotency_key"])

    op.add_column("outbox_events", sa.Column("leased_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("outbox_events", sa.Column("lease_holder", sa.String(100), nullable=True))
    op.create_index("ix_outbox_events_lease", "outbox_events", ["leased_at", "lease_holder"])

    op.add_column("tasks", sa.Column("recovery_key", sa.String(128), nullable=True))
    op.create_unique_constraint("uq_tasks_recovery_key", "tasks", ["recovery_key"])
    op.create_index("ix_tasks_recovery_key", "tasks", ["recovery_key"])


def downgrade() -> None:
    op.drop_index("ix_tasks_recovery_key", table_name="tasks")
    op.drop_constraint("uq_tasks_recovery_key", "tasks", type_="unique")
    op.drop_column("tasks", "recovery_key")

    op.drop_index("ix_outbox_events_lease", table_name="outbox_events")
    op.drop_column("outbox_events", "lease_holder")
    op.drop_column("outbox_events", "leased_at")

    op.drop_index("ix_outbox_events_idempotency_key", table_name="outbox_events")
    op.drop_constraint("uq_outbox_events_idempotency_key", "outbox_events", type_="unique")
    op.drop_column("outbox_events", "idempotency_key")
