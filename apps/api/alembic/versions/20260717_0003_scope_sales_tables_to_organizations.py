"""scope sales tables to organizations

Revision ID: 20260717_0003
Revises: 20260717_0002
Create Date: 2026-07-17 01:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260717_0003"
down_revision: str | None = "20260717_0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("organizations", sa.Column("clerk_org_id", sa.String(length=255), nullable=True))
    op.create_index(op.f("ix_organizations_clerk_org_id"), "organizations", ["clerk_org_id"], unique=True)

    op.add_column("companies", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.add_column("opportunities", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.add_column("tasks", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.add_column("activities", sa.Column("organization_id", sa.Integer(), nullable=True))

    op.execute(
        sa.text(
            """
            INSERT INTO organizations (name, slug)
            SELECT 'Pacific North Systems', 'pacific-north-systems'
            WHERE NOT EXISTS (SELECT 1 FROM organizations)
            """
        )
    )

    op.execute(
        sa.text(
            """
            UPDATE companies
            SET organization_id = (SELECT id FROM organizations ORDER BY id ASC LIMIT 1)
            WHERE organization_id IS NULL
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE opportunities
            SET organization_id = COALESCE(
                (SELECT companies.organization_id FROM companies WHERE companies.id = opportunities.company_id),
                (SELECT id FROM organizations ORDER BY id ASC LIMIT 1)
            )
            WHERE organization_id IS NULL
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE tasks
            SET organization_id = COALESCE(
                (SELECT companies.organization_id FROM companies WHERE companies.id = tasks.company_id),
                (SELECT id FROM organizations ORDER BY id ASC LIMIT 1)
            )
            WHERE organization_id IS NULL
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE activities
            SET organization_id = COALESCE(
                (SELECT companies.organization_id FROM companies WHERE companies.id = activities.company_id),
                (SELECT id FROM organizations ORDER BY id ASC LIMIT 1)
            )
            WHERE organization_id IS NULL
            """
        )
    )

    op.alter_column("companies", "organization_id", nullable=False)
    op.alter_column("opportunities", "organization_id", nullable=False)
    op.alter_column("tasks", "organization_id", nullable=False)
    op.alter_column("activities", "organization_id", nullable=False)

    op.create_index(op.f("ix_companies_organization_id"), "companies", ["organization_id"], unique=False)
    op.create_index(op.f("ix_opportunities_organization_id"), "opportunities", ["organization_id"], unique=False)
    op.create_index(op.f("ix_tasks_organization_id"), "tasks", ["organization_id"], unique=False)
    op.create_index(op.f("ix_activities_organization_id"), "activities", ["organization_id"], unique=False)

    op.create_foreign_key(
        "fk_companies_organization_id_organizations",
        "companies",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_opportunities_organization_id_organizations",
        "opportunities",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_tasks_organization_id_organizations",
        "tasks",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_activities_organization_id_organizations",
        "activities",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_activities_organization_id_organizations", "activities", type_="foreignkey")
    op.drop_constraint("fk_tasks_organization_id_organizations", "tasks", type_="foreignkey")
    op.drop_constraint("fk_opportunities_organization_id_organizations", "opportunities", type_="foreignkey")
    op.drop_constraint("fk_companies_organization_id_organizations", "companies", type_="foreignkey")

    op.drop_index(op.f("ix_activities_organization_id"), table_name="activities")
    op.drop_index(op.f("ix_tasks_organization_id"), table_name="tasks")
    op.drop_index(op.f("ix_opportunities_organization_id"), table_name="opportunities")
    op.drop_index(op.f("ix_companies_organization_id"), table_name="companies")

    op.drop_column("activities", "organization_id")
    op.drop_column("tasks", "organization_id")
    op.drop_column("opportunities", "organization_id")
    op.drop_column("companies", "organization_id")

    op.drop_index(op.f("ix_organizations_clerk_org_id"), table_name="organizations")
    op.drop_column("organizations", "clerk_org_id")