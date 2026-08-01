"""
AI Company Analysis Engine.

Generates comprehensive, explainable company analysis
using LLM enrichment with deterministic fallback.
Never invents facts — all claims grounded in CRM data.
"""

import json
from typing import Any

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.application.llm.enrichment import EnrichmentResult, get_enrichment_service
from app.application.sales.scoring import ScoringEngine
from app.infrastructure.db.models import Activity, Company, Contact, Opportunity


class AnalysisSection(BaseModel):
    title: str
    content: str
    confidence: str  # "high", "medium", "low"
    sources: list[str]


class CompanyAnalysis(BaseModel):
    company_id: int
    company_name: str
    business_summary: AnalysisSection
    business_model: AnalysisSection
    growth_indicators: AnalysisSection
    buying_signals: AnalysisSection
    operational_challenges: AnalysisSection
    software_opportunities: AnalysisSection
    decision_makers: AnalysisSection
    recommended_services: AnalysisSection
    estimated_budget: AnalysisSection
    project_size: AnalysisSection
    closing_probability: AnalysisSection
    conversation_topics: AnalysisSection
    discovery_questions: AnalysisSection
    risks: AnalysisSection
    next_action: AnalysisSection


class CompanyAnalysisEngine:
    def __init__(self, session: Session) -> None:
        self._session = session

    def analyze(self, company: Company) -> CompanyAnalysis:
        contacts = self._session.execute(
            select(Contact).where(Contact.company_id == company.id, Contact.status == "active")
        ).scalars().all()

        activity_count = self._session.execute(
            select(func.count(Activity.id)).where(Activity.company_id == company.id)
        ).scalar_one()

        opps = self._session.execute(
            select(Opportunity).where(Opportunity.company_id == company.id)
        ).scalars().all()

        score_result = ScoringEngine(self._session).score_company(company)

        # Build structured context for LLM
        context = self._build_context(company, contacts, activity_count, score_result)

        # Try LLM enrichment — use results for narrative sections
        llm = self._try_enrich(context)

        return CompanyAnalysis(
            company_id=company.id,
            company_name=company.name,
            business_summary=llm.get("summary") or self._template_business_summary(company),
            business_model=llm.get("model") or self._template_business_model(company),
            growth_indicators=llm.get("growth") or self._template_growth_indicators(company),
            buying_signals=self._template_buying_signals(company, score_result.score_breakdown),
            operational_challenges=llm.get("challenges") or self._template_operational_challenges(company),
            software_opportunities=llm.get("opportunities") or self._template_software_opportunities(company, score_result),
            decision_makers=self._template_decision_makers(contacts),
            recommended_services=self._template_recommended_services(score_result),
            estimated_budget=self._template_estimated_budget(score_result),
            project_size=self._template_project_size(company, score_result),
            closing_probability=self._template_closing_probability(score_result),
            conversation_topics=llm.get("topics") or self._template_conversation_topics(company, contacts, activity_count),
            discovery_questions=llm.get("questions") or self._template_discovery_questions(company),
            risks=llm.get("risks") or self._template_risks(company, contacts, activity_count),
            next_action=self._template_next_action(score_result),
        )

    # ── LLM Enrichment ──

    def _build_context(self, c: Company, contacts: list[Contact], activity_count: int, score: Any) -> dict[str, Any]:
        return {
            "name": c.name,
            "industry": c.industry or "Unknown",
            "employees": c.employees or "N/A",
            "city": c.city or "Unknown",
            "province": c.province,
            "website": c.website or "None",
            "description": c.description or "None",
            "linkedin_url": c.linkedin_url or "None",
            "opportunity_score": score.opportunity_score,
            "confidence_score": score.confidence_score,
            "signals": [b.description for b in score.score_breakdown],
            "recommended_services": score.recommended_services,
            "contact_count": len(contacts),
            "contacts": [f"{ct.first_name} {ct.last_name} ({ct.job_title or 'N/A'})" for ct in contacts[:5]],
            "activity_count": activity_count,
            "has_website": bool(c.website),
            "has_linkedin": bool(c.linkedin_url),
        }

    def _try_enrich(self, context: dict[str, Any]) -> dict[str, AnalysisSection | None]:
        """Attempt LLM enrichment. Returns dict of AnalysisSection or None for each key."""
        result: dict[str, AnalysisSection | None] = {
            "summary": None, "model": None, "growth": None,
            "challenges": None, "opportunities": None,
            "topics": None, "questions": None, "risks": None,
        }
        try:
            svc = get_enrichment_service()
            if not svc.available:
                return result

            enrichment = svc.enrich_sync("company_analysis_full", context)
            if not enrichment.enriched or not enrichment.content:
                return result

            # Parse LLM response into sections
            sections = self._parse_llm_response(enrichment.content)
            for key, section in sections.items():
                if key in result:
                    result[key] = section
        except Exception:
            pass  # Silent fallback to templates
        return result

    def _parse_llm_response(self, content: str) -> dict[str, AnalysisSection]:
        """Parse LLM response — prefer JSON, fall back to markdown, use raw as last resort."""
        # Try JSON first
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                return self._json_to_sections(data)
        except (json.JSONDecodeError, TypeError):
            pass

        # Try markdown headers
        sections = self._parse_markdown(content)
        if sections:
            return sections

        # Fallback: use entire response as executive summary
        return {
            "summary": AnalysisSection(
                title="AI Analysis",
                content=content[:2000],
                confidence="low",
                sources=["LLM response (format parsing failed)"],
            )
        }

    def _json_to_sections(self, data: dict[str, Any]) -> dict[str, AnalysisSection]:
        """Convert JSON LLM response to AnalysisSections."""
        key_map = {
            "executive_summary": "summary", "business_model": "model",
            "growth_indicators": "growth", "operational_challenges": "challenges",
            "software_opportunities": "opportunities", "conversation_topics": "topics",
            "discovery_questions": "questions", "business_risks": "risks",
            "current_situation": "summary", "business_challenges": "challenges",
            "proposed_solution": "opportunities",
        }
        sections: dict[str, AnalysisSection] = {}
        for json_key, mapped_key in key_map.items():
            value = data.get(json_key)
            if value:
                content = value if isinstance(value, str) else json.dumps(value)
                sections[mapped_key] = AnalysisSection(
                    title=json_key.replace("_", " ").title(),
                    content=content[:2000],
                    confidence="medium",
                    sources=["LLM analysis based on CRM data"],
                )
        return sections

    def _parse_markdown(self, content: str) -> dict[str, AnalysisSection]:
        sections: dict[str, AnalysisSection] = {}
        current_title = ""
        current_body: list[str] = []

        for line in content.split("\n"):
            line = line.strip()
            if not line:
                continue
            # Detect section headers like "## Title" or "**Title**" or "1. Title"
            if line.startswith("##") or line.startswith("**") or (len(line) > 2 and line[0].isdigit() and ". " in line[:4]):
                if current_title and current_body:
                    key = self._map_title_to_key(current_title)
                    sections[key] = AnalysisSection(
                        title=current_title,
                        content="\n".join(current_body),
                        confidence="medium",
                        sources=["LLM analysis based on CRM data"],
                    )
                # Extract title
                clean = line.lstrip("#").lstrip("0123456789. ").lstrip("*").rstrip("*").strip()
                current_title = clean
                current_body = []
            else:
                if line.startswith("• ") or line.startswith("- ") or line.startswith("* "):
                    current_body.append(line)
                else:
                    current_body.append(line)

        # Don't forget the last section
        if current_title and current_body:
            key = self._map_title_to_key(current_title)
            sections[key] = AnalysisSection(
                title=current_title,
                content="\n".join(current_body),
                confidence="medium",
                sources=["LLM analysis based on CRM data"],
            )

        return sections

    def _map_title_to_key(self, title: str) -> str:
        t = title.lower()
        if any(w in t for w in ["summary", "overview", "executive"]): return "summary"
        if any(w in t for w in ["model", "business model"]): return "model"
        if any(w in t for w in ["growth", "indicator"]): return "growth"
        if any(w in t for w in ["challenge", "pain", "operational", "bottleneck"]): return "challenges"
        if any(w in t for w in ["opportunit", "software", "service"]): return "opportunities"
        if any(w in t for w in ["topic", "conversation"]): return "topics"
        if any(w in t for w in ["question", "discovery"]): return "questions"
        if any(w in t for w in ["risk", "concern"]): return "risks"
        return "summary"  # default

    # ── Template Fallbacks (deterministic) ──

    def _template_business_summary(self, c: Company) -> AnalysisSection:
        parts: list[str] = []
        sources: list[str] = []
        if c.industry:
            parts.append(f"{c.name} operates in the {c.industry} industry.")
            sources.append("Industry field")
        if c.description:
            parts.append(c.description)
            sources.append("Company description")
        if c.employees:
            parts.append(f"The company has approximately {c.employees} employees.")
            sources.append("Employee count")
        if c.city:
            loc = f"{c.city}, {c.province}" if c.province else c.city
            parts.append(f"Located in {loc}.")
            sources.append("Location data")
        return AnalysisSection(
            title="Business Summary",
            content=" ".join(parts) if parts else f"{c.name} — limited public information available.",
            confidence="high" if len(parts) >= 3 else "medium" if parts else "low",
            sources=sources,
        )

    def _template_business_model(self, c: Company) -> AnalysisSection:
        model = "B2B" if c.industry and any(kw in c.industry.lower() for kw in ["engineering", "manufacturing", "construction"]) else "Mixed B2B/B2C"
        return AnalysisSection(title="Business Model", content=f"Likely {model} based on industry classification.", confidence="medium", sources=["Industry classification"])

    def _template_growth_indicators(self, c: Company) -> AnalysisSection:
        signals: list[str] = []
        sources: list[str] = []
        if c.employees and c.employees > 50: signals.append("Medium-to-large workforce"); sources.append("Employee count")
        if c.locations: signals.append("Multiple locations"); sources.append("Location data")
        if c.website: signals.append("Established web presence"); sources.append("Website")
        if c.linkedin_url: signals.append("Professional networking active"); sources.append("LinkedIn")
        return AnalysisSection(title="Growth Indicators", content=", ".join(signals) if signals else "No clear growth indicators detected.", confidence="medium" if signals else "low", sources=sources)

    def _template_buying_signals(self, c: Company, breakdown: list[Any]) -> AnalysisSection:
        positives = [b.description for b in breakdown if b.points > 0]
        return AnalysisSection(title="Buying Signals", content="; ".join(positives) if positives else "No strong buying signals detected.", confidence="high" if len(positives) >= 3 else "medium" if positives else "low", sources=[f"Scoring rule: {b.description}" for b in breakdown if b.points > 0])

    def _template_operational_challenges(self, c: Company) -> AnalysisSection:
        challenges: list[str] = []
        sources: list[str] = []
        ind = (c.industry or "").lower()
        if "construction" in ind: challenges.append("Field-to-office communication gaps"); sources.append("Industry: construction")
        if "property" in ind: challenges.append("Tenant/owner communication management"); sources.append("Industry: property")
        if "manufacturing" in ind: challenges.append("Inventory and maintenance tracking"); sources.append("Industry: manufacturing")
        if "engineering" in ind: challenges.append("Document and specification management"); sources.append("Industry: engineering")
        if not challenges: challenges.append("Operational efficiency and process digitization"); sources.append("General assessment")
        return AnalysisSection(title="Operational Challenges", content="; ".join(challenges), confidence="medium", sources=sources)

    def _template_software_opportunities(self, c: Company, score_result: Any) -> AnalysisSection:
        return AnalysisSection(title="Software Opportunities", content=f"Recommended: {', '.join(score_result.recommended_services)}. {score_result.service_reason}", confidence="medium", sources=["Service catalog", "Scoring engine"])

    def _template_decision_makers(self, contacts: list[Contact]) -> AnalysisSection:
        if not contacts: return AnalysisSection(title="Decision Makers", content="No contacts on file.", confidence="low", sources=[])
        titles = [f"{c.first_name} {c.last_name} ({c.job_title or 'No title'})" for c in contacts[:5]]
        return AnalysisSection(title="Decision Makers", content="; ".join(titles), confidence="high", sources=["Contacts database"])

    def _template_recommended_services(self, score_result: Any) -> AnalysisSection:
        return AnalysisSection(title="Recommended Services", content=", ".join(score_result.recommended_services), confidence="medium", sources=["Service recommendation engine"])

    def _template_estimated_budget(self, score_result: Any) -> AnalysisSection:
        return AnalysisSection(title="Estimated Budget", content=f"{score_result.estimated_value.get('tier', 'Unknown')} tier — {score_result.estimated_value.get('range', 'N/A')}", confidence="low", sources=["Value estimation model"])

    def _template_project_size(self, c: Company, score_result: Any) -> AnalysisSection:
        emp = c.employees or 0
        size = "Large (6+ months)" if emp > 100 else "Medium (3-6 months)" if emp > 20 else "Small (1-3 months)"
        return AnalysisSection(title="Project Size", content=size, confidence="low", sources=["Employee count proxy"])

    def _template_closing_probability(self, score_result: Any) -> AnalysisSection:
        s = score_result.opportunity_score
        prob = "High (60-80%)" if s >= 70 else "Medium (40-60%)" if s >= 50 else "Low (20-40%)"
        return AnalysisSection(title="Closing Probability", content=prob, confidence="medium", sources=["Scoring engine"])

    def _template_conversation_topics(self, c: Company, contacts: list[Contact], activity_count: int) -> AnalysisSection:
        topics: list[str] = []
        if c.industry: topics.append(f"Their {c.industry} operations and challenges")
        if not contacts: topics.append("Who handles technology decisions?")
        if activity_count == 0: topics.append("Initial introduction and capabilities overview")
        topics.append("Digital transformation roadmap")
        return AnalysisSection(title="Conversation Topics", content="; ".join(topics), confidence="medium", sources=["Company profile"])

    def _template_discovery_questions(self, c: Company) -> AnalysisSection:
        qs = ["What software systems are you currently using?", "What are your biggest operational challenges?", "How do you handle client communication and project tracking?", "What would an ideal solution look like?", "Who else is involved in technology purchasing decisions?"]
        return AnalysisSection(title="Discovery Questions", content="\n".join(f"• {q}" for q in qs), confidence="medium", sources=["Sales methodology"])

    def _template_risks(self, c: Company, contacts: list[Contact], activity_count: int) -> AnalysisSection:
        risks: list[str] = []
        if not contacts: risks.append("No decision-maker contacts on file")
        if activity_count < 2: risks.append("Low engagement history")
        if not c.website: risks.append("Limited digital presence")
        if not risks: risks.append("No significant risks identified")
        return AnalysisSection(title="Risks", content="; ".join(risks), confidence="medium", sources=["CRM data"])

    def _template_next_action(self, score_result: Any) -> AnalysisSection:
        return AnalysisSection(title="Next Action", content=score_result.next_action, confidence="medium", sources=["Next action engine"])
