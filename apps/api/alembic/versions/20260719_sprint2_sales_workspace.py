"""sprint2_sales_workspace

Revision ID: sprint2_001
Revises: 20260717_0003
Create Date: 2026-07-19

- Add contacts table
- Enhance activities (company_id → NOT NULL, add contact_id, subject, body, completed_at)
- Enhance tasks (add contact_id, description, priority, status)
- Enhance opportunities (add contact_id, title, estimated_value, probability, expected_close_date, owner, stage, notes, updated_at)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "sprint2_001"
down_revision: Union[str, None] = "20260717_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Contacts
    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("first_name", sa.String(120), nullable=False),
        sa.Column("last_name", sa.String(120), nullable=False),
        sa.Column("job_title", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("mobile", sa.String(50), nullable=True),
        sa.Column("linkedin", sa.String(255), nullable=True),
        sa.Column("preferred_contact", sa.String(20), nullable=True),
        sa.Column("is_decision_maker", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_contacts_company_id"), "contacts", ["company_id"])
    op.create_index(op.f("ix_contacts_organization_id"), "contacts", ["organization_id"])
    op.create_index(op.f("ix_contacts_id"), "contacts", ["id"])

    # Activities: make company_id NOT NULL, add new columns
    op.alter_column("activities", "company_id", existing_type=sa.Integer(), nullable=False)
    op.add_column("activities", sa.Column("contact_id", sa.Integer(), nullable=True))
    op.add_column("activities", sa.Column("subject", sa.String(255), nullable=True))
    op.add_column("activities", sa.Column("body", sa.Text(), nullable=True))
    op.add_column("activities", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(None, "activities", "contacts", ["contact_id"], ["id"], ondelete="SET NULL")

    # Tasks: add new columns
    op.add_column("tasks", sa.Column("contact_id", sa.Integer(), nullable=True))
    op.add_column("tasks", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("tasks", sa.Column("priority", sa.String(20), nullable=False, server_default="medium"))
    op.add_column("tasks", sa.Column("status", sa.String(20), nullable=False, server_default="open"))
    op.create_foreign_key(None, "tasks", "contacts", ["contact_id"], ["id"], ondelete="SET NULL")

    # Opportunities: add new columns to replace old ones
    op.add_column("opportunities", sa.Column("contact_id", sa.Integer(), nullable=True))
    op.add_column("opportunities", sa.Column("title", sa.String(255), nullable=False, server_default="Untitled"))
    op.add_column("opportunities", sa.Column("estimated_value", sa.Numeric(14, 2), nullable=False, server_default="0"))
    op.add_column("opportunities", sa.Column("probability", sa.Integer(), nullable=False, server_default="50"))
    op.add_column("opportunities", sa.Column("expected_close_date", sa.Date(), nullable=True))
    op.add_column("opportunities", sa.Column("owner", sa.String(255), nullable=True))
    op.add_column("opportunities", sa.Column("stage", sa.String(20), nullable=False, server_default="lead"))
    op.add_column("opportunities", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column("opportunities", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(None, "opportunities", "contacts", ["contact_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    op.drop_table("contacts")
    op.drop_constraint(None, "activities", type_="foreignkey")
    op.drop_column("activities", "completed_at")
    op.drop_column("activities", "body")
    op.drop_column("activities", "subject")
    op.drop_column("activities", "contact_id")
    op.alter_column("activities", "company_id", existing_type=sa.Integer(), nullable=True)
    op.drop_constraint(None, "tasks", type_="foreignkey")
    op.drop_column("tasks", "status")
    op.drop_column("tasks", "priority")
    op.drop_column("tasks", "description")
    op.drop_column("tasks", "contact_id")
    op.drop_constraint(None, "opportunities", type_="foreignkey")
    op.drop_column("opportunities", "updated_at")
    op.drop_column("opportunities", "notes")
    op.drop_column("opportunities", "stage")
    op.drop_column("opportunities", "owner")
    op.drop_column("opportunities", "expected_close_date")
    op.drop_column("opportunities", "probability")
    op.drop_column("opportunities", "estimated_value")
    op.drop_column("opportunities", "title")
    op.drop_column("opportunities", "contact_id")
