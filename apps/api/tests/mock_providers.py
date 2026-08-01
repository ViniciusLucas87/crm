"""
Deterministic mock implementations for offline testing.

All providers return predictable, pre-defined responses.
No external services, credentials, or randomness required.
"""

from app.application.llm.provider import LLMConfig, LLMMessage, LLMProvider, LLMResponse


class DeterministicLLMProvider(LLMProvider):
    """Returns predictable JSON responses for Conversation Intelligence tests.

    Matches the expected insight categories from the acceptance test
    construction company conversation.
    """

    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)

    async def chat(self, messages, tools=None, tool_choice="auto") -> LLMResponse:
        """Return deterministic intelligence based on transcript content."""
        content = ""
        for msg in messages:
            if msg.role == "user":
                content = msg.content
                break

        response = self._analyze(content)
        return LLMResponse(content=response, finish_reason="stop")

    async def chat_stream(self, messages, tools=None, tool_choice="auto"):
        response = await self.chat(messages, tools, tool_choice)
        yield response.content

    def _analyze(self, text: str) -> str:
        """Simple keyword-based analysis for deterministic testing."""
        import json

        insights = []
        text_lower = text.lower()

        # Pain points
        if "manual" in text_lower or "paper" in text_lower or "paperwork" in text_lower:
            insights.append({
                "category": "pain_point", "value": "Manual paperwork process",
                "confidence": 90, "evidence": "Everything is done manually",
                "speaker": "Customer",
            })
        if "scheduling" in text_lower:
            insights.append({
                "category": "pain_point", "value": "Scheduling difficulties",
                "confidence": 85, "evidence": "Scheduling is a nightmare",
                "speaker": "Customer",
            })

        # Software
        if "jobber" in text_lower:
            insights.append({
                "category": "current_software", "value": "Jobber",
                "confidence": 95, "evidence": "We use Jobber for scheduling",
                "speaker": "Customer",
            })
        if "quickbooks" in text_lower:
            insights.append({
                "category": "current_software", "value": "QuickBooks",
                "confidence": 95, "evidence": "QuickBooks for accounting",
                "speaker": "Customer",
            })
        if "excel" in text_lower:
            insights.append({
                "category": "current_software", "value": "Excel",
                "confidence": 95, "evidence": "Excel for everything else",
                "speaker": "Customer",
            })

        # Process
        if "manual" in text_lower:
            insights.append({
                "category": "current_process", "value": "Manual inspections",
                "confidence": 90, "evidence": "Everything is done manually",
                "speaker": "Customer",
            })

        # Decision maker
        if "operations director" in text_lower or "mike" in text_lower:
            insights.append({
                "category": "decision_maker", "value": "Mike Reynolds, Operations Director",
                "confidence": 95, "evidence": "Our Operations Director, Mike Reynolds",
                "speaker": "Customer",
            })

        # Budget
        if "forty thousand" in text_lower or "$40" in text_lower or "40000" in text_lower:
            insights.append({
                "category": "budget", "value": "$40,000",
                "confidence": 90, "evidence": "allocated around forty thousand dollars",
                "speaker": "Customer",
            })

        # Timeline
        if "next quarter" in text_lower:
            insights.append({
                "category": "timeline", "value": "Next quarter",
                "confidence": 80, "evidence": "Ideally next quarter",
                "speaker": "Customer",
            })

        # Company info
        if "65" in text or "sixty five" in text_lower:
            insights.append({
                "category": "goal", "value": "65 employees, residential and commercial",
                "confidence": 90, "evidence": "construction company with around 65 employees",
                "speaker": "Customer",
            })

        # Risk from missed deadline
        if "missed" in text_lower or "deadline" in text_lower:
            insights.append({
                "category": "risk", "value": "Missed inspection deadline cost contract",
                "confidence": 85, "evidence": "missed an inspection deadline because the paperwork got lost",
                "speaker": "Customer",
            })

        return json.dumps({
            "insights": insights,
            "summary": "Construction company with manual processes, using Jobber/QuickBooks/Excel. Pain points: scheduling and paperwork. Decision maker: Operations Director. Budget: $40K. Timeline: next quarter.",
        })
