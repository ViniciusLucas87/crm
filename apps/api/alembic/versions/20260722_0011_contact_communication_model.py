"""contact communication model — Sprint 31 data refactor

Revision ID: 20260722_0011
Revises: 20260722_0010
Create Date: 2026-07-23

Adds is_primary, department, confidence, discovery_source to contacts.
Adds primary_contact_id to companies.
Migrates existing company phone/email to primary contacts.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260722_0011"
down_revision: Union[str, None] = "20260722_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Add columns to contacts ──
    op.add_column("contacts", sa.Column("department", sa.String(120), nullable=True))
    op.add_column("contacts", sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("contacts", sa.Column("confidence", sa.String(20), nullable=False, server_default="manual"))
    op.add_column("contacts", sa.Column("discovery_source", sa.String(50), nullable=True))
    op.create_index("ix_contacts_is_primary", "contacts", ["is_primary"])

    # ── Add primary_contact_id to companies ──
    op.add_column("companies", sa.Column("primary_contact_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_companies_primary_contact", "companies", "contacts", ["primary_contact_id"], ["id"], ondelete="SET NULL")

    # ── Migrate existing company phone/email to a primary contact ──
    conn = op.get_bind()
    companies = conn.execute(
        sa.text("SELECT id, organization_id, name, phone, email FROM companies WHERE phone IS NOT NULL OR email IS NOT NULL")
    ).fetchall()

    for company in companies:
        cid, org_id, name, phone, email = company

        # Check if this company already has contacts
        existing = conn.execute(
            sa.text("SELECT id FROM contacts WHERE company_id = :cid LIMIT 1"),
            {"cid": cid},
        ).fetchone()

        if existing:
            # Set first contact as primary and update its phone/email
            conn.execute(
                sa.text(
                    "UPDATE contacts SET is_primary = true, phone = COALESCE(phone, :phone), email = COALESCE(email, :email) WHERE id = :id"
                ),
                {"phone": phone, "email": email, "id": existing[0]},
            )
            conn.execute(
                sa.text("UPDATE companies SET primary_contact_id = :contact_id WHERE id = :cid"),
                {"contact_id": existing[0], "cid": cid},
            )
        elif phone or email:
            # Create a placeholder contact from company data
            result = conn.execute(
                sa.text(
                    "INSERT INTO contacts (organization_id, company_id, first_name, last_name, phone, email, is_primary, confidence) "
                    "VALUES (:org_id, :cid, :first_name, :last_name, :phone, :email, true, 'manual') RETURNING id"
                ),
                {
                    "org_id": org_id,
                    "cid": cid,
                    "first_name": name,
                    "last_name": "Contact",
                    "phone": phone,
                    "email": email,
                },
            )
            contact_id = result.fetchone()[0]
            conn.execute(
                sa.text("UPDATE companies SET primary_contact_id = :contact_id WHERE id = :cid"),
                {"contact_id": contact_id, "cid": cid},
            )


def downgrade() -> None:
    op.drop_constraint("fk_companies_primary_contact", "companies", type_="foreignkey")
    op.drop_column("companies", "primary_contact_id")
    op.drop_index("ix_contacts_is_primary", table_name="contacts")
    op.drop_column("contacts", "discovery_source")
    op.drop_column("contacts", "confidence")
    op.drop_column("contacts", "is_primary")
    op.drop_column("contacts", "department")
