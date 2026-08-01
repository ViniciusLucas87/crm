"""add sprint42 columns to transcripts and transcript_segments

Revision ID: 20260723_sprint42
Revises: 20260722_0006
Create Date: 2026-07-23
"""

from collections.abc import Sequence
from alembic import op

revision: str = "20260723_sprint42"
down_revision: str | None = "20260722_0013"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # Add columns to transcripts (use IF NOT EXISTS for safety)
    op.execute("ALTER TABLE transcripts ADD COLUMN IF NOT EXISTS company_id INTEGER REFERENCES companies(id) ON DELETE SET NULL")
    op.execute("ALTER TABLE transcripts ADD COLUMN IF NOT EXISTS contact_id INTEGER REFERENCES contacts(id) ON DELETE SET NULL")
    op.execute("ALTER TABLE transcripts ADD COLUMN IF NOT EXISTS provider_transcript_id VARCHAR(255)")
    op.execute("ALTER TABLE transcripts ADD COLUMN IF NOT EXISTS full_text TEXT")
    op.execute("ALTER TABLE transcripts ADD COLUMN IF NOT EXISTS word_count INTEGER DEFAULT 0")
    op.execute("ALTER TABLE transcripts ADD COLUMN IF NOT EXISTS utterance_count INTEGER DEFAULT 0")
    op.execute("ALTER TABLE transcripts ADD COLUMN IF NOT EXISTS started_at TIMESTAMP WITH TIME ZONE")
    op.execute("ALTER TABLE transcripts ADD COLUMN IF NOT EXISTS ended_at TIMESTAMP WITH TIME ZONE")
    op.execute("ALTER TABLE transcripts ADD COLUMN IF NOT EXISTS duration_seconds INTEGER DEFAULT 0")
    op.execute("ALTER TABLE transcripts ADD COLUMN IF NOT EXISTS recording_url VARCHAR(1000)")
    op.execute("ALTER TABLE transcripts ADD COLUMN IF NOT EXISTS recording_enabled BOOLEAN DEFAULT false")
    op.execute("ALTER TABLE transcripts ADD COLUMN IF NOT EXISTS diarization_enabled BOOLEAN DEFAULT true")
    op.execute("ALTER TABLE transcripts ADD COLUMN IF NOT EXISTS metadata_json TEXT")

    # Add columns to transcript_segments
    op.execute("ALTER TABLE transcript_segments ADD COLUMN IF NOT EXISTS organization_id INTEGER")
    op.execute("ALTER TABLE transcript_segments ADD COLUMN IF NOT EXISTS speaker_label VARCHAR(120)")
    op.execute("ALTER TABLE transcript_segments ADD COLUMN IF NOT EXISTS words_json TEXT")
    op.execute("ALTER TABLE transcript_segments ADD COLUMN IF NOT EXISTS language VARCHAR(10)")
    op.execute("ALTER TABLE transcript_segments ADD COLUMN IF NOT EXISTS segment_id VARCHAR(100)")

    # Create indexes
    op.execute("CREATE INDEX IF NOT EXISTS idx_transcripts_company ON transcripts(company_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_transcripts_contact ON transcripts(contact_id)")


def downgrade() -> None:
    # We don't drop columns — they can stay
    pass
