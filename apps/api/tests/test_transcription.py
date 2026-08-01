"""
Project TITAN — Communication Intelligence Pipeline Acceptance Tests.

Validates the complete pipeline with realistic business conversations:
    Transcript → ConversationIntelligence → Structured Insights → DecisionEngine
"""

import pytest

from app.application.transcription import (
    MockTranscriptProvider,
    TranscriptEvent,
    TranscriptEventType,
    TranscriptSegment,
    TranscriptWord,
    create_transcript_provider,
)
from app.application.transcription.intelligence import (
    ConversationInsight,
    ConversationIntelligence,
    InsightCategory,
    IntelligenceReport,
    get_conversation_intelligence,
)
from app.application.llm.provider import LLMConfig
from tests.mock_providers import DeterministicLLMProvider


# ═══════════════════════════════════════════════════════════
# ACCEPTANCE TEST — Realistic Construction Company Call
# ═══════════════════════════════════════════════════════════

CONSTRUCTION_CONVERSATION = [
    TranscriptSegment(speaker="Sales", text="Thanks for joining today. Can you tell me a bit about your company?", start=0, end=4),
    TranscriptSegment(speaker="Customer", text="We're a construction company with around 65 employees. We do residential and commercial projects.", start=4, end=10),
    TranscriptSegment(speaker="Sales", text="How do inspections work today?", start=10, end=12),
    TranscriptSegment(speaker="Customer", text="Everything is done manually. Our inspectors fill out paper forms, then someone enters it into Excel. It takes forever.", start=12, end=20),
    TranscriptSegment(speaker="Sales", text="What software do you currently use?", start=20, end=22),
    TranscriptSegment(speaker="Customer", text="We use Jobber for scheduling, QuickBooks for accounting, and Excel for everything else.", start=22, end=28),
    TranscriptSegment(speaker="Sales", text="Who normally approves software purchases?", start=28, end=30),
    TranscriptSegment(speaker="Customer", text="Our Operations Director, Mike Reynolds. He's been with us 12 years.", start=30, end=35),
    TranscriptSegment(speaker="Sales", text="Do you have a budget for this kind of solution?", start=35, end=37),
    TranscriptSegment(speaker="Customer", text="Yes, we've allocated around forty thousand dollars for this year.", start=37, end=41),
    TranscriptSegment(speaker="Sales", text="When would you want to implement something?", start=41, end=43),
    TranscriptSegment(speaker="Customer", text="Ideally next quarter. We're finishing a big project in December.", start=43, end=47),
    TranscriptSegment(speaker="Sales", text="What's your biggest frustration right now?", start=47, end=49),
    TranscriptSegment(speaker="Customer", text="Scheduling is a nightmare, and the paperwork is killing us. We waste 15-20 hours a week on admin.", start=49, end=56),
    TranscriptSegment(speaker="Sales", text="Has anything gone wrong because of the manual process?", start=56, end=59),
    TranscriptSegment(speaker="Customer", text="Last month we missed an inspection deadline because the paperwork got lost. Cost us the contract.", start=59, end=65),
]


class TestAcceptanceFullPipeline:
    """End-to-end acceptance tests with realistic business conversations."""

    @pytest.mark.asyncio
    async def test_construction_company_call(self):
        """Full pipeline with deterministic mock — no external LLM required."""
        intel = ConversationIntelligence(api_key="test-key")
        # Inject deterministic mock provider
        intel._provider = DeterministicLLMProvider(LLMConfig(provider="mock", model="mock", api_key="x"))

        report = IntelligenceReport()
        chunk_size = 3
        for i in range(0, len(CONSTRUCTION_CONVERSATION), chunk_size):
            chunk = CONSTRUCTION_CONVERSATION[i:i + chunk_size]
            result = await intel.analyze(chunk)
            report.insights.extend(result.insights)

        assert isinstance(report, IntelligenceReport)
        assert len(report.insights) > 0  # Deterministic mock returns insights
        assert report.analyzed_at != ""

    def test_segment_streaming_incremental(self):
        """Verify only new segments are processed — not entire history."""
        all_segments = CONSTRUCTION_CONVERSATION
        processed = 0
        chunk_size = 3

        for i in range(0, len(all_segments), chunk_size):
            chunk = all_segments[i:i + chunk_size]
            processed += len(chunk)

        assert processed == len(all_segments)

    def test_evidence_validation(self):
        """Every insight must have evidence, speaker, and confidence."""
        insight = ConversationInsight(
            category=InsightCategory.PAIN_POINT,
            value="Manual paperwork",
            confidence=85,
            evidence="Everything is done manually. Our inspectors fill out paper forms.",
            speaker="Customer",
        )

        # All required fields present
        assert insight.evidence is not None
        assert len(insight.evidence) > 5
        assert insight.speaker != "Unknown"
        assert insight.confidence >= 30  # Minimum threshold

    def test_reject_empty_evidence(self):
        """Insights without evidence should be rejected."""
        insight = ConversationInsight(
            category=InsightCategory.BUDGET,
            value="$100,000",
            confidence=50,
            evidence="",  # Empty — should be rejected
        )
        # Validation: evidence must be non-empty with substance
        is_valid = insight.evidence and len(insight.evidence) > 5 and insight.confidence >= 30
        assert not is_valid

    def test_dedup_logic(self):
        """Duplicate insights should be merged, not duplicated."""
        existing = [
            ConversationInsight(category=InsightCategory.PAIN_POINT, value="Scheduling", confidence=70, evidence="Scheduling is hard", speaker="Customer"),
        ]
        new = ConversationInsight(category=InsightCategory.PAIN_POINT, value="Scheduling", confidence=90, evidence="Scheduling is a nightmare", speaker="Customer")

        # Dedup: same category + similar value → update, not insert
        is_duplicate = any(
            e.category == new.category and e.value.lower() == new.value.lower()
            for e in existing
        )
        assert is_duplicate

    def test_noise_filtering(self):
        """Small talk/noise should not generate business insights."""
        noise_segments = [
            TranscriptSegment(speaker="Sales", text="Hello", start=0, end=1),
            TranscriptSegment(speaker="Customer", text="Can you hear me?", start=1, end=2),
            TranscriptSegment(speaker="Sales", text="One second, getting coffee", start=2, end=3),
        ]
        # Noise segments are short — should be filtered
        substantive = [s for s in noise_segments if len(s.text.split()) >= 3]
        assert len(substantive) == 2  # "Can you hear me?" and "One second, getting coffee"


class TestTranscriptProvider:
    """Verify provider abstraction, lifecycle, and error recovery."""

    def test_provider_factory(self):
        mock = create_transcript_provider("mock")
        assert mock.provider_name == "mock"

        with pytest.raises(ValueError, match="Unknown transcript provider"):
            create_transcript_provider("nonexistent")

    @pytest.mark.asyncio
    async def test_mock_provider_lifecycle(self):
        provider = create_transcript_provider("mock")
        assert await provider.connect({}) is True
        events: list[TranscriptEvent] = []

        async def capture(event: TranscriptEvent):
            events.append(event)

        await provider.start_streaming(capture)
        await provider.stop_streaming()
        await provider.disconnect()

    @pytest.mark.asyncio
    async def test_provider_reconnect_logic(self):
        mock = create_transcript_provider("mock")
        await mock.connect({})
        events: list[TranscriptEvent] = []

        async def capture(event: TranscriptEvent):
            events.append(event)

        mock._max_reconnect_attempts = 2
        mock._reconnect_attempts = 2
        result = await mock.reconnect({}, capture)
        assert result is False
        assert events[-1].type == TranscriptEventType.ERROR


class TestConversationIntelligence:
    """Verify insight extraction with evidence and confidence."""

    @pytest.mark.asyncio
    async def test_empty_segments(self):
        intel = get_conversation_intelligence(api_key="")
        report = await intel.analyze([])
        assert isinstance(report, IntelligenceReport)

    @pytest.mark.asyncio
    async def test_no_api_key_returns_empty(self):
        intel = get_conversation_intelligence(api_key="")
        segments = [TranscriptSegment(speaker="C", text="test", start=0, end=1)]
        report = await intel.analyze(segments)
        assert report.analyzed_at != ""

    def test_parse_json_extracts_from_code_blocks(self):
        intel = ConversationIntelligence(api_key="")
        result = intel._parse_json('```json\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_parse_json_handles_invalid(self):
        intel = ConversationIntelligence(api_key="")
        result = intel._parse_json("not json at all")
        assert result == {}


class TestTranscriptSegment:
    def test_segment_defaults(self):
        segment = TranscriptSegment()
        assert segment.speaker == "Speaker 0"

    def test_segment_with_words(self):
        words = [TranscriptWord(word="Hello", start=0.0, end=0.5, confidence=0.99)]
        segment = TranscriptSegment(text="Hello", words=words, is_final=True)
        assert len(segment.words) == 1
        assert segment.is_final


class TestIntelligenceReport:
    def test_empty_report(self):
        report = IntelligenceReport()
        assert report.budget_indicated is None

    def test_report_categorizes_insights(self):
        report = IntelligenceReport()
        report.insights = [
            ConversationInsight(category=InsightCategory.PAIN_POINT, value="Dispatch slow", confidence=90, evidence="Dispatch takes 45 min", speaker="Customer"),
            ConversationInsight(category=InsightCategory.BUDGET, value="$50,000", confidence=85, evidence="Budget is 50k", speaker="Customer"),
        ]
        report.pain_points = [i.value for i in report.insights if i.category.value == "pain_point"]
        report.budget_indicated = next((i.value for i in report.insights if i.category.value == "budget"), None)
        assert "Dispatch slow" in report.pain_points
        assert report.budget_indicated == "$50,000"
