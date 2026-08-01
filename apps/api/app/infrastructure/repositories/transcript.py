"""Transcript repository — persistence for transcripts and segments."""

import logging
from datetime import UTC, datetime
from typing import Sequence

from sqlalchemy import select, func, update
from sqlalchemy.orm import Session

from app.infrastructure.db.models import Transcript, TranscriptSegment

logger = logging.getLogger(__name__)


class TranscriptRepository:
    """Repository for transcript persistence."""

    def __init__(self, db: Session):
        self._db = db

    # ── Transcript CRUD ──

    def create_transcript(
        self,
        organization_id: int,
        *,
        call_id: int | None = None,
        company_id: int | None = None,
        contact_id: int | None = None,
        conversation_id: int | None = None,
        provider: str = "deepgram",
        language: str = "en",
        diarization_enabled: bool = True,
        recording_enabled: bool = False,
    ) -> Transcript:
        t = Transcript(
            organization_id=organization_id,
            call_id=call_id,
            company_id=company_id,
            contact_id=contact_id,
            conversation_id=conversation_id,
            provider=provider,
            language=language,
            diarization_enabled=diarization_enabled,
            recording_enabled=recording_enabled,
            status="in_progress",
            started_at=datetime.now(UTC),
        )
        self._db.add(t)
        self._db.flush()
        return t

    def get_transcript(self, transcript_id: int) -> Transcript | None:
        return self._db.get(Transcript, transcript_id)

    def get_transcripts_by_call(self, call_id: int) -> Sequence[Transcript]:
        return self._db.scalars(
            select(Transcript).where(Transcript.call_id == call_id).order_by(Transcript.created_at.desc())
        ).all()

    def get_transcripts_by_company(self, company_id: int, limit: int = 50) -> Sequence[Transcript]:
        return self._db.scalars(
            select(Transcript)
            .where(Transcript.company_id == company_id)
            .order_by(Transcript.created_at.desc())
            .limit(limit)
        ).all()

    def get_transcripts_by_org(self, organization_id: int, limit: int = 50, offset: int = 0) -> Sequence[Transcript]:
        return self._db.scalars(
            select(Transcript)
            .where(Transcript.organization_id == organization_id)
            .order_by(Transcript.created_at.desc())
            .offset(offset)
            .limit(limit)
        ).all()

    def count_transcripts_by_org(self, organization_id: int) -> int:
        return self._db.scalar(
            select(func.count()).select_from(Transcript).where(Transcript.organization_id == organization_id)
        ) or 0

    def complete_transcript(
        self, transcript_id: int, *, full_text: str = "", word_count: int = 0, utterance_count: int = 0, duration_seconds: int = 0
    ) -> Transcript | None:
        t = self.get_transcript(transcript_id)
        if t:
            t.status = "completed"
            t.ended_at = datetime.now(UTC)
            if full_text:
                t.full_text = full_text
            t.word_count = word_count
            t.utterance_count = utterance_count
            t.duration_seconds = duration_seconds
            self._db.flush()
        return t

    def update_transcript_status(self, transcript_id: int, status: str) -> None:
        self._db.execute(
            update(Transcript).where(Transcript.id == transcript_id).values(status=status, updated_at=datetime.now(UTC))
        )

    def search_transcripts(self, organization_id: int, query: str, limit: int = 20) -> Sequence[Transcript]:
        return self._db.scalars(
            select(Transcript)
            .where(
                Transcript.organization_id == organization_id,
                Transcript.full_text.ilike(f"%{query}%"),
            )
            .order_by(Transcript.created_at.desc())
            .limit(limit)
        ).all()

    # ── Segment (Utterance) CRUD ──

    def add_utterance(
        self,
        organization_id: int,
        transcript_id: int,
        *,
        speaker: str = "Speaker 0",
        speaker_label: str | None = None,
        text: str = "",
        is_final: bool = False,
        confidence: float = 0.0,
        start_time: float = 0.0,
        end_time: float = 0.0,
        sequence: int = 0,
        words_json: str | None = None,
        language: str | None = None,
        segment_id: str | None = None,
    ) -> TranscriptSegment:
        u = TranscriptSegment(
            organization_id=organization_id,
            transcript_id=transcript_id,
            speaker=speaker,
            speaker_label=speaker_label,
            text=text,
            is_final=is_final,
            confidence=confidence,
            start_time=start_time,
            end_time=end_time,
            sequence=sequence,
            words_json=words_json,
            language=language,
            segment_id=segment_id,
        )
        self._db.add(u)
        self._db.flush()
        return u

    def get_segments(self, transcript_id: int) -> Sequence[TranscriptSegment]:
        return self._db.scalars(
            select(TranscriptSegment)
            .where(TranscriptSegment.transcript_id == transcript_id)
            .order_by(TranscriptSegment.start_time)
        ).all()

    def get_final_segments(self, transcript_id: int) -> Sequence[TranscriptSegment]:
        return self._db.scalars(
            select(TranscriptSegment)
            .where(TranscriptSegment.transcript_id == transcript_id, TranscriptSegment.is_final == True)
            .order_by(TranscriptSegment.start_time)
        ).all()

    def update_segment_text(self, segment_id: int, text: str, is_final: bool = False, confidence: float = 0.0) -> None:
        values = {"text": text}
        if is_final:
            values["is_final"] = True
        if confidence:
            values["confidence"] = confidence
        self._db.execute(update(TranscriptSegment).where(TranscriptSegment.id == segment_id).values(**values))

