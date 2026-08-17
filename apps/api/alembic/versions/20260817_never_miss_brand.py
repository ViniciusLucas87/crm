"""Consolidate product branding under Never Miss.

Revision ID: 20260817_never_miss_brand
Revises: 20260817_products_mvp
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260817_never_miss_brand"
down_revision: str | None = "20260817_products_mvp"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Preserve any existing Plus intake key before removing the old product row.
    op.execute(
        """
        UPDATE product_configurations AS target
        SET intake_key_hash = COALESCE(target.intake_key_hash, source.intake_key_hash),
            plan = 'never_miss_plus'
        FROM product_configurations AS source
        WHERE target.organization_id = source.organization_id
          AND target.product_code = 'never_miss'
          AND source.product_code = 'lead_capture'
        """
    )
    op.execute(
        """
        DELETE FROM product_configurations AS source
        USING product_configurations AS target
        WHERE target.organization_id = source.organization_id
          AND target.product_code = 'never_miss'
          AND source.product_code = 'lead_capture'
        """
    )
    op.execute(
        """
        UPDATE product_configurations
        SET product_code = 'never_miss', plan = 'never_miss_plus'
        WHERE product_code = 'lead_capture'
        """
    )
    op.execute(
        """
        UPDATE product_configurations
        SET plan = CASE
            WHEN plan IN ('recover', 'convert') THEN 'never_miss_plus'
            ELSE 'never_miss'
        END
        WHERE plan IN ('pilot', 'capture', 'recover', 'convert')
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE product_configurations
        SET plan = 'pilot'
        WHERE plan IN ('never_miss', 'never_miss_plus')
        """
    )
