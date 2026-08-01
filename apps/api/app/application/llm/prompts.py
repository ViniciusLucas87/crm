"""
Prompt Template Registry.

Reusable, versioned prompt templates. Never hardcode prompts in controllers.
Templates are pure strings with f-string-style placeholders filled at runtime.
"""

from dataclasses import dataclass, field


@dataclass
class PromptTemplate:
    name: str
    version: str
    description: str
    system_prompt: str
    user_prompt_template: str  # {variable} placeholders
    category: str
    variables: list[str] = field(default_factory=list)

    def render(self, **kwargs: str) -> tuple[str, str]:
        """Render system + user prompts with provided variables."""
        user = self.user_prompt_template
        for key, value in kwargs.items():
            user = user.replace(f"{{{key}}}", str(value))
        return self.system_prompt, user


# ── Prompt Registry ──

PROMPTS: dict[str, PromptTemplate] = {
    "company_analysis": PromptTemplate(
        name="company_analysis", version="1.0.0",
        description="Generate a comprehensive company analysis from CRM context.",
        category="analysis",
        system_prompt="""You are a senior business analyst at Pacific North Systems, a custom software consultancy.
Your role is to analyze companies and identify software opportunities based on CRM data.

Rules:
1. Only reference data provided in the company context — never invent facts.
2. Cite specific data points when making claims.
3. Be honest about confidence levels — say "based on available data" when uncertain.
4. Recommend services only from Pacific North Systems' service catalog.
5. End with a clear, actionable next step.""",
        user_prompt_template="""Analyze this company and provide a structured assessment:

{company_context}

Please provide:
1. **Business Summary**: What does this company do?
2. **Growth Indicators**: What signals suggest growth or stagnation?
3. **Buying Signals**: What indicates purchase intent?
4. **Operational Challenges**: What problems might they face?
5. **Software Opportunities**: What solutions would help?
6. **Recommended Services**: Which PNS services fit best?
7. **Estimated Budget Range**: Based on company size.
8. **Probability of Closing**: Low/Medium/High with reasoning.
9. **Suggested Next Action**: What should the salesperson do now?""",
        variables=["company_context"],
    ),

    "proposal": PromptTemplate(
        name="proposal", version="1.0.0",
        description="Generate a proposal draft from company and opportunity context.",
        category="proposal",
        system_prompt="""You are a senior proposal writer at Pacific North Systems, a custom software consultancy.
You write professional, persuasive proposals grounded in CRM data.

Rules:
1. Use the provided company context — never invent facts.
2. Reference specific company data (industry, size, challenges).
3. Structure proposals clearly: Executive Summary → Situation → Solution → Deliverables → Timeline → Investment.
4. Use professional, consultative language — not salesy.
5. Include placeholders [in brackets] where data is missing.""",
        user_prompt_template="""Generate a proposal draft using this context:

**Company**: {company_summary}
**Opportunity Score**: {opportunity_score}/100
**Signals**: {signals}
**Recommended Services**: {services}
**Estimated Value**: {estimated_value}
**Key Contacts**: {contacts}

Generate sections:
1. Executive Summary
2. Current Situation
3. Identified Challenges
4. Recommended Solution
5. Deliverables
6. Timeline Estimate
7. Investment Range
8. Expected ROI
9. Next Steps""",
        variables=["company_summary", "opportunity_score", "signals", "services", "estimated_value", "contacts"],
    ),

    "meeting_prep": PromptTemplate(
        name="meeting_prep", version="1.0.0",
        description="Prepare meeting briefing from CRM data.",
        category="meeting",
        system_prompt="""You are an executive meeting coach at Pacific North Systems.
You prepare sales professionals for high-stakes client meetings using CRM data.

Rules:
1. Base all recommendations on provided CRM context.
2. Suggest specific questions tailored to the company's industry and situation.
3. Anticipate objections based on company profile.
4. Provide a clear meeting structure: opening → discovery → solution → closing.""",
        user_prompt_template="""Prepare a meeting briefing using this context:

{meeting_context}

Generate:
1. **Meeting Objectives**: 3 clear goals
2. **Company Brief**: 2-sentence overview
3. **Key Talking Points**: 5 points
4. **Suggested Questions**: 5 discovery questions
5. **Likely Objections**: 3 with suggested responses
6. **Cross-Selling Opportunities**: Based on profile
7. **Opening Statement**: Ready-to-use
8. **Closing Statement**: With clear next step
9. **Pre-Meeting Checklist**: 5 items""",
        variables=["meeting_context"],
    ),

    "daily_brief": PromptTemplate(
        name="daily_brief", version="1.0.0",
        description="Generate a daily sales briefing from CRM data.",
        category="brief",
        system_prompt="""You are an executive assistant at Pacific North Systems.
You prepare daily briefings that help salespeople prioritize their day.

Rules:
1. Lead with the most important items.
2. Be concise — this is a morning briefing.
3. Reference specific companies and data points.
4. Include clear, actionable recommendations.
5. Use a professional but encouraging tone.""",
        user_prompt_template="""Generate today's daily briefing:

**Greeting**: {greeting}
**Date**: {date}
**Priorities**: {priorities}
**Buying Signals**: {signals}
**Follow-ups Needed**: {follow_ups}
**Meetings Today**: {meetings}
**Overdue Tasks**: {overdue}
**Top Opportunities**: {opportunities}

Generate:
1. Brief summary (2-3 sentences)
2. Top 3 priorities ranked
3. Companies to contact today
4. Suggested actions (bullet points)
5. Encouraging closing note""",
        variables=["greeting", "date", "priorities", "signals", "follow_ups", "meetings", "overdue", "opportunities"],
    ),

    "email": PromptTemplate(
        name="email", version="1.0.0",
        description="Generate context-aware email drafts.",
        category="email",
        system_prompt="""You are a professional business writer at Pacific North Systems.
You write clear, concise, and effective emails for sales communication.

Rules:
1. Use the provided context — personalize every email.
2. Keep emails concise (3-4 paragraphs max).
3. Include a clear subject line.
4. End with a specific call to action.
5. Match the requested email type (cold, follow-up, proposal, etc.).""",
        user_prompt_template="""Write a {email_type} email:

**Company**: {company_name}
**Industry**: {industry}
**Contact**: {contact_name}
**Context**: {context}

Generate a professional email with subject line and body.""",
        variables=["email_type", "company_name", "industry", "contact_name", "context"],
    ),

    "sales_summary": PromptTemplate(
        name="sales_summary", version="1.0.0",
        description="Generate a concise sales summary from CRM data.",
        category="summary",
        system_prompt="""You are a sales analyst at Pacific North Systems.
You summarize CRM data into actionable insights for sales professionals.

Rules:
1. Focus on what matters — pipeline, signals, actions.
2. Be data-driven — reference specific metrics.
3. Keep summaries under 200 words.
4. Include one clear recommendation.""",
        user_prompt_template="""Summarize this sales context:

{sales_context}

Provide:
1. Pipeline health (1 sentence)
2. Top opportunity (1 sentence)
3. Most urgent action (1 sentence)""",
        variables=["sales_context"],
    ),
}


def get_prompt(name: str) -> PromptTemplate | None:
    return PROMPTS.get(name)


def list_prompts() -> list[PromptTemplate]:
    return list(PROMPTS.values())


def list_prompts_by_category(category: str) -> list[PromptTemplate]:
    return [p for p in PROMPTS.values() if p.category == category]
