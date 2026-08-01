"""conversation engine

Revision ID: 20260722_0010
Revises: 20260722_0009
Create Date: 2026-07-22

Introduces the Conversation model — the business relationship abstraction
above CallSession. Adds conversation_id to calls, activities, and tasks.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260722_0010"
down_revision: Union[str, None] = "20260722_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Conversations table ──
    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("primary_contact_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("relationship_stage", sa.String(20), nullable=False, server_default="new"),
        sa.Column("opened_by", sa.String(255), nullable=True),
        sa.Column("owner", sa.String(255), nullable=True),
        sa.Column("health_score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["primary_contact_id"], ["contacts.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_conversations_id", "conversations", ["id"])
    op.create_index("ix_conversations_org", "conversations", ["organization_id"])
    op.create_index("ix_conversations_company", "conversations", ["company_id"])
    op.create_index("ix_conversations_stage", "conversations", ["relationship_stage"])

    # ── Add conversation_id to calls ──
    op.add_column("calls", sa.Column("conversation_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_calls_conversation", "calls", "conversations", ["conversation_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_calls_conversation", "calls", ["conversation_id"])

    # ── Add conversation_id to activities ──
    op.add_column("activities", sa.Column("conversation_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_activities_conversation", "activities", "conversations", ["conversation_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_activities_conversation", "activities", ["conversation_id"])

    # ── Add conversation_id to tasks ──
    op.add_column("tasks", sa.Column("conversation_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_tasks_conversation", "tasks", "conversations", ["conversation_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_tasks_conversation", "tasks", ["conversation_id"])


def downgrade() -> None:
    op.drop_index("ix_tasks_conversation", table_name="tasks")
    op.drop_constraint("fk_tasks_conversation", "tasks", type_="foreignkey")
    op.drop_column("tasks", "conversation_id")

    op.drop_index("ix_activities_conversation", table_name="activities")
    op.drop_constraint("fk_activities_conversation", "activities", type_="foreignkey")
    op.drop_column("activities", "conversation_id")

    op.drop_index("ix_calls_conversation", table_name="calls")
    op.drop_constraint("fk_calls_conversation", "calls", type_="foreignkey")
    op.drop_column("calls", "conversation_id")

    op.drop_table("conversations")
