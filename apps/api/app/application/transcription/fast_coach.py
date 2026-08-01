"""
Sprint 47.7 — FastCoachEngine v3 (Deal-Narrative-Driven Commercial Coach)

Integrated with DealNarrativeEngine, NextCommitmentEngine, and RapportIntelligenceEngine.
Every recommendation contributes to the active deal strategy.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any

from app.application.transcription.coaching_contract import CoachingRecommendation
from app.application.transcription.deal_narrative import DealNarrativeEngine, DealNarrative
from app.application.transcription.commitment_engine import NextCommitmentEngine, CommitmentRecommendation, CLOSE_TEMPLATES
from app.application.transcription.rapport_intelligence import RapportIntelligenceEngine, RapportSuggestion


# ═══════════════════════════════════════════════════════════
# COMMERCIALLY-DRIVEN RESPONSE TEMPLATES
# ═══════════════════════════════════════════════════════════

def _cost_clarify_response(evidence: str) -> CoachingRecommendation:
    """Detected a quantified cost — clarify its composition."""
    return CoachingRecommendation(
        semantic_key="cost_clarify",
        title="Clarify the cost composition",
        action="Understand what drives the quantified cost",
        suggested_wording="What contributes most to that cost each month — administrative time, delays, errors, or rework?",
        reason="Understanding cost composition identifies the highest-value automation target and builds the business case.",
        evidence=evidence,
        expected_outcome="Clear breakdown of cost drivers, enabling precise solution targeting.",
        priority="critical",
        confidence=88,
        alternatives=[
            "How much of that cost is labour versus delays or errors?",
            "Which part of that cost would you most want to reduce?",
            "Is that cost consistent month to month, or does it vary?",
        ],
        expires_when="Cost composition understood",
        category="quantification",
        stage="pain_points",
        transition="That helps us focus on the right area.",
    )

def _urgency_response(evidence: str) -> CoachingRecommendation:
    """Cost is quantified — establish urgency."""
    return CoachingRecommendation(
        semantic_key="urgency_establish",
        title="Establish urgency",
        action="Ask whether this is a priority",
        suggested_wording="Is reducing that cost already a priority for this quarter, or is this something you're evaluating for later?",
        reason="Quantified pain without urgency doesn't drive decisions. Understanding their timeline reveals whether this is active or passive.",
        evidence=evidence,
        expected_outcome="Clear urgency signal: active priority vs. future consideration.",
        priority="high",
        confidence=85,
        alternatives=[
            "How long has this been creating that level of cost, and is there already an internal plan to address it?",
            "What would happen if this continued at the current cost for another six months?",
        ],
        expires_when="Urgency is clear",
        category="urgency",
        stage="timeline",
        transition="That helps me understand the priority level.",
    )

def _solution_align_response(evidence: str) -> CoachingRecommendation:
    """Urgency established — align the solution hypothesis."""
    return CoachingRecommendation(
        semantic_key="solution_align",
        title="Align the solution",
        action="Connect their problem to a practical PNS approach",
        suggested_wording="Based on what you described, the opportunity may not be replacing everything. It may be removing the manual handoff between the field work and the reporting — capturing the information once and automating what happens afterward.",
        reason="Positioning the solution as targeted improvement rather than wholesale replacement reduces perceived risk.",
        evidence=evidence,
        expected_outcome="Prospect sees a practical, scoped path forward rather than an overwhelming project.",
        priority="high",
        confidence=83,
        alternatives=[
            "The biggest impact could come from automating just that one handoff. Would you like to explore what that would look like?",
            "There may be an opportunity to solve the specific bottleneck without disrupting the rest of your operation.",
        ],
        expires_when="Solution aligned",
        category="solution",
        stage="solution",
        transition="Let me share what the next step typically looks like.",
    )

def _micro_commitment_response(narrative: DealNarrative) -> CoachingRecommendation | None:
    """Recommend the next appropriate micro-commitment."""
    mc = narrative.micro_commitments
    
    if not mc:
        return CoachingRecommendation(
            semantic_key="micro_commit_agree_problem",
            title="Confirm the problem is meaningful",
            action="Get agreement that the problem is worth addressing",
            suggested_wording="Would you say this is one of the bigger operational challenges your team faces, or are there other priorities that rank higher?",
            reason="Confirmation that the problem matters is the foundation for all further commitment.",
            evidence="Problem identified",
            expected_outcome="Prospect confirms this is a meaningful issue worth addressing.",
            priority="medium",
            confidence=78,
            category="micro_commitment",
            stage="pain_points",
        )
    
    if "problem_confirmed" not in [str(m) for m in mc] and narrative.operational_problem:
        narrative.add_micro_commitment("problem_confirmed")
    
    if narrative.quantified_cost and "cost_acknowledged" not in [str(m) for m in mc]:
        return CoachingRecommendation(
            semantic_key="micro_commit_confirm_impact",
            title="Confirm the impact is understood",
            action="Get agreement on the quantified impact",
            suggested_wording="So it sounds like the manual process is costing roughly that amount each month. Would you agree that's a fair estimate of the operational impact?",
            reason="Shared understanding of the cost creates alignment and justifies further exploration.",
            evidence=narrative.quantified_cost,
            expected_outcome="Prospect confirms the cost estimate and agrees it's significant.",
            priority="medium",
            confidence=82,
            category="micro_commitment",
            stage="pain_points",
        )
    
    if narrative.urgency != "unknown" and "urgency_acknowledged" not in [str(m) for m in mc]:
        return CoachingRecommendation(
            semantic_key="micro_commit_urgency",
            title="Confirm the timing",
            action="Lock in the urgency signal",
            suggested_wording="Great — so this is something you'd like to address in the near term. That helps me think about the right approach.",
            reason="Acknowledged urgency creates momentum for a concrete next step.",
            evidence=f"Urgency: {narrative.urgency}",
            expected_outcome="Prospect confirms this is a near-term priority.",
            priority="medium",
            confidence=80,
            category="micro_commitment",
            stage="timeline",
        )
    
    if narrative.solution_hypothesis and "improvement_worthwhile" not in [str(m) for m in mc]:
        return CoachingRecommendation(
            semantic_key="micro_commit_worthwhile",
            title="Confirm improvement is worthwhile",
            action="Get agreement that solving this would be valuable",
            suggested_wording="Based on what we've discussed, it sounds like reducing that manual handoff would make a meaningful difference. Would you agree?",
            reason="Explicit confirmation of value creates readiness for the next step.",
            evidence=narrative.solution_hypothesis,
            expected_outcome="Prospect agrees improvement is worthwhile.",
            priority="high",
            confidence=83,
            category="micro_commitment",
            stage="solution",
        )
    
    return None


# ═══════════════════════════════════════════════════════════
# STAGE GUIDANCE (commercially-focused)
# ═══════════════════════════════════════════════════════════

STAGE_GUIDE = {
    "opening": CoachingRecommendation(
        semantic_key="stage_opening", title="Set the agenda clearly",
        action="Establish purpose and earn permission",
        suggested_wording="Before we dive in, let me share what I'd like to cover today. Then I'd love to hear about your priorities.",
        reason="Setting clear expectations builds trust and gives the prospect a roadmap.",
        evidence="Call opening",
        expected_outcome="Prospect understands the call structure and feels in control.",
        priority="medium", confidence=80,
        alternatives=["I'd like to understand your current process, then share how we might help."],
        expires_when="Agenda is set",
        category="stage", stage="opening",
    ),
    "rapport": CoachingRecommendation(
        semantic_key="stage_rapport", title="Build genuine connection",
        action="Find professional common ground",
        suggested_wording="Before we get into the details — how has business been for your team recently?",
        reason="Natural opener creates comfort and reveals operational context.",
        evidence="Call is in rapport stage",
        expected_outcome="Prospect relaxes and shares current business context.",
        priority="medium", confidence=75,
        alternatives=["What's been keeping your team busy lately?"],
        expires_when="Rapport established",
        category="stage", stage="rapport",
        transition="That's helpful. Could you walk me through how that process works today?",
    ),
    "discovery": CoachingRecommendation(
        semantic_key="stage_discovery", title="Map the current workflow",
        action="Walk through their process step by step",
        suggested_wording="Can you walk me through how you handle that currently, from start to finish?",
        reason="You need to understand the actual workflow before suggesting changes.",
        evidence="Ready to explore current process",
        expected_outcome="Complete process map with roles, steps, tools, and handoffs.",
        priority="high", confidence=82,
        alternatives=["What does a typical day look like for the team involved?"],
        expires_when="Process fully mapped",
        category="stage", stage="discovery",
        transition="That gives me a clear picture. Where does that create the most friction?",
    ),
    "pain_points": CoachingRecommendation(
        semantic_key="stage_pain_points", title="Uncover the real frustration",
        action="Ask where the process breaks down",
        suggested_wording="What's the most time-consuming or frustrating part of that process?",
        reason="Find the specific pain that creates enough motivation to change.",
        evidence="Process has been described",
        expected_outcome="Identified specific pain point with owner, frequency, and impact.",
        priority="high", confidence=83,
        alternatives=["Where do you see the most mistakes or delays?"],
        expires_when="Pain point identified",
        category="stage", stage="pain_points",
        transition="That's exactly the kind of problem we help solve.",
    ),
    "solution": CoachingRecommendation(
        semantic_key="stage_solution", title="Present relevantly",
        action="Connect capabilities to their specific needs",
        suggested_wording="Based on what you've shared, the opportunity may be to capture the information once in the field and automate the reporting afterward — rather than replacing everything at once.",
        reason="Targeted solution reduces perceived risk and shows you listened.",
        evidence="Discovery complete, pain points clear",
        expected_outcome="Prospect sees direct connection between their problem and PNS.",
        priority="critical", confidence=85,
        alternatives=["The biggest impact could come from automating just that one handoff."],
        expires_when="Solution presented",
        category="stage", stage="solution",
        transition="The next useful step would be to show you this in action.",
    ),
    "closing": CoachingRecommendation(
        semantic_key="stage_closing", title="Define concrete next steps",
        action="Lock in a specific follow-up",
        suggested_wording="The next useful step would be to map this workflow together and show you a practical example. Would next Tuesday or Wednesday work?",
        reason="Specificity creates momentum. A vague 'let's follow up' loses deals.",
        evidence="Solution value established",
        expected_outcome="Specific meeting scheduled.",
        priority="critical", confidence=88,
        alternatives=["I can prepare a scoped proposal based on the workflow we discussed."],
        expires_when="Next meeting scheduled",
        category="stage", stage="closing",
    ),
}


class FastCoachEngine:
    """Commercial-outcome-driven coaching engine. No LLM. Sub-150ms.
    
    Integrated with DealNarrativeEngine, NextCommitmentEngine, RapportIntelligenceEngine.
    Every recommendation contributes to an active deal strategy.
    """
    
    def __init__(self):
        self._agent_words = 0
        self._prospect_words = 0
        self._agent_utterances = 0
        self._prospect_utterances = 0
        self._segment_count = 0
        self._last_prospect_text: str = ""
        self._stage: str = "opening"
        self._discovered: set[str] = set()
        self._last_result: CoachingRecommendation | None = None
        self._result_history: list[str] = []
        self._both_channels_live: bool = False
        self._first_segment_time: float = 0.0
        self._grace_period_seconds: float = 12.0
        
        # Sprint 47.7 — commercial engines
        self._narrative_engine = DealNarrativeEngine()
        self._commitment_engine = NextCommitmentEngine()
        self._rapport = RapportIntelligenceEngine()
        self._company_context: dict = {}
    
    def set_company_context(self, ctx: dict):
        self._company_context = ctx
        self._rapport.set_company_context(ctx)
    
    def set_contact_context(self, ctx: dict):
        self._rapport.set_contact_context(ctx)
    
    @property
    def talk_ratio(self) -> float:
        total = self._agent_words + self._prospect_words
        return self._agent_words / total if total > 0 else 0.5
    
    @property
    def in_grace_period(self) -> bool:
        if not self._both_channels_live: return True
        if self._first_segment_time == 0: return True
        return False  # Grace period handled separately
    
    @property
    def narrative(self) -> DealNarrative:
        return self._narrative_engine.narrative
    
    def process(self, segment: dict) -> CoachingRecommendation | None:
        """Process a finalized segment. Produces commercially-driven recommendation."""
        self._segment_count += 1
        
        text = segment.get("text", "")
        text_lower = text.lower()
        role = segment.get("source_role", segment.get("speaker", "unknown"))
        end_time = segment.get("end", 0)
        
        is_prospect = role in ("prospect", "customer", "1") or "customer" in str(role).lower()
        
        word_count = len(text.split())
        if not is_prospect:
            self._agent_words += word_count
            self._agent_utterances += 1
        else:
            self._prospect_words += word_count
            self._prospect_utterances += 1
            self._last_prospect_text = text
        
        if self._first_segment_time == 0: self._first_segment_time = end_time
        if self._agent_utterances > 0 and self._prospect_utterances > 0:
            self._both_channels_live = True
        
        # ── Update deal narrative from prospect speech ──
        if is_prospect:
            self._narrative_engine.update_from_segment(text, is_prospect)
        
        # ── Stage detection ──
        old_stage = self._stage
        self._detect_stage(text_lower)
        stage_changed = self._stage != old_stage
        
        # ── 1. Quantified cost detected → clarify composition (CRITICAL) ──
        if self._narrative_engine.narrative.quantified_cost and text == self._last_prospect_text:
            result = _cost_clarify_response(text[:200])
            return self._dedup_and_return(result)
        
        # ── 2. Keyword-triggered responses ──
        result = self._match_keywords(text_lower, text)
        if result:
            return self._dedup_and_return(result)
        
        # ── 3. Narrative gap → highest-value gap question ──
        gaps = self._narrative_engine.narrative.narrative_gaps
        if gaps:
            result = self._gap_question(gaps[0])
            if result:
                return self._dedup_and_return(result)
        
        # ── 4. Micro-commitment → next appropriate commitment ──
        result = _micro_commitment_response(self._narrative_engine.narrative)
        if result:
            return self._dedup_and_return(result)
        
        # ── 5. Close readiness → recommend commitment ──
        close_rec = self._commitment_engine.determine(self._narrative_engine.narrative)
        if close_rec.commitment_type != "continue_discovery" and close_rec.suggested_wording:
            result = CoachingRecommendation(
                semantic_key=f"close_{close_rec.commitment_type}",
                title=close_rec.title,
                action="Secure the next commitment",
                suggested_wording=close_rec.suggested_wording,
                reason=close_rec.reason,
                evidence=f"Close readiness: {self._narrative_engine.narrative.close_readiness}",
                expected_outcome="Next meeting or commitment secured.",
                priority="critical",
                confidence=close_rec.confidence,
                alternatives=close_rec.alternatives,
                expires_when="Commitment achieved",
                category="closing",
                stage="closing",
                transition="",
            )
            return self._dedup_and_return(result)
        
        # ── 6. Stage guidance ──
        if stage_changed or self._segment_count % 3 == 0:
            result = STAGE_GUIDE.get(self._stage)
            if result:
                return self._dedup_and_return(result)
        
        # ── 7. First segment — rapport ──
        if self._segment_count <= 2:
            suggestion = self._rapport.generate_opener()
            if suggestion:
                result = CoachingRecommendation(
                    semantic_key="rapport_opener", title="Open the conversation",
                    action="Start with a natural opener",
                    suggested_wording=suggestion.suggested_opener,
                    reason=f"Industry-appropriate opening.",
                    evidence="Call start",
                    expected_outcome="Prospect engages.",
                    priority="medium", confidence=suggestion.confidence,
                    category="rapport", stage="opening",
                    transition=suggestion.transition,
                )
                return self._dedup_and_return(result)
        
        return None
    
    def _match_keywords(self, text_lower: str, original: str) -> CoachingRecommendation | None:
        """Keyword matching with commercially-aware responses."""
        # Paper/forms — detect workflow problem
        if any(w in text_lower for w in ["paper form", "paper", "print", "handwritten"]):
            return CoachingRecommendation(
                semantic_key="paper_workflow", title="Explore the paper workflow",
                action="Ask what happens after paper forms",
                suggested_wording="What happens to those paper forms after the technician completes them? Who enters the information and where?",
                reason="This reveals duplicate data entry — the most common source of operational waste.",
                evidence=original[:200],
                expected_outcome="Identify manual handoff, responsible roles, and time cost.",
                priority="high", confidence=88,
                alternatives=["Who enters that data afterward?", "How long does that handoff typically take?", "Where do errors usually happen?"],
                expires_when="Paper workflow mapped",
                category="manual_workflow", stage="discovery",
                transition="That helps me see where the process could be improved.",
            )
        
        # Spreadsheet — data handoff
        if any(w in text_lower for w in ["spreadsheet", "excel", "sheets"]):
            return CoachingRecommendation(
                semantic_key="spreadsheet_handoff", title="Explore the data handoff",
                action="Ask how data moves from field to spreadsheet",
                suggested_wording="How does the data get from the field into the spreadsheet — who enters it and how long does it take?",
                reason="The manual handoff between operations and administration is usually the most expensive bottleneck.",
                evidence=original[:200],
                expected_outcome="Quantify data entry step and identify automation potential.",
                priority="high", confidence=87,
                alternatives=["Who updates the spreadsheet and how often?", "What happens when multiple people need the same information?"],
                expires_when="Data entry understood",
                category="manual_workflow", stage="discovery",
            )
        
        # Budget objection
        if any(w in text_lower for w in ["too expensive", "can't afford", "not in budget"]):
            self._narrative_engine.add_objection(original[:200])
            return CoachingRecommendation(
                semantic_key="budget_objection", title="Budget concern — reframe to value",
                action="Ask about current process cost",
                suggested_wording="Before we discuss implementation cost — what does the current manual process cost your team in staff time each month?",
                reason="Shift from price objection to cost-of-current-process comparison.",
                evidence=original[:200],
                expected_outcome="Prospect sees cost of inaction vs. investment.",
                priority="critical", confidence=90,
                alternatives=["What would it mean if this problem were solved?"],
                expires_when="Budget objection resolved",
                category="objection", stage="budget",
            )
        
        # Pain point
        if any(w in text_lower for w in ["problem", "challenge", "issue", "struggling", "pain", "headache"]):
            return CoachingRecommendation(
                semantic_key="pain_deep", title="Go deeper on the pain point",
                action="Quantify impact",
                suggested_wording="How often does that happen, and what does it cost your team in time or money when it does?",
                reason="Moving from identifying pain to quantifying impact builds the business case.",
                evidence=original[:200],
                expected_outcome="Measurable impact: frequency, cost, who is affected.",
                priority="high", confidence=85,
                alternatives=["What have you tried?", "What would solving this mean for daily work?"],
                expires_when="Pain quantified",
                category="pain_point", stage="pain_points",
            )
        
        # Timeline
        if any(w in text_lower for w in ["timeline", "deadline", "next quarter", "urgent"]):
            return CoachingRecommendation(
                semantic_key="timeline_qualify", title="Qualify the timeline",
                action="Understand what's driving their timeline",
                suggested_wording="What's driving that timeline on your end — is there a specific event or deadline you're working toward?",
                reason="Understanding the real driver reveals whether timeline is aspirational or mandatory.",
                evidence=original[:200],
                expected_outcome="Real deadline and consequences of missing it.",
                priority="high", confidence=83,
                alternatives=["What happens if you don't have a solution by then?"],
                expires_when="Timeline clear",
                category="timeline_mention", stage="timeline",
            )
        
        # Decision maker
        if any(w in text_lower for w in ["decision maker", "my boss", "approval", "sign off"]):
            return CoachingRecommendation(
                semantic_key="decision_maker_engage", title="Engage the decision maker",
                action="Ask what they need to see",
                suggested_wording="What would they need to see to feel confident moving forward?",
                reason="Turning decision makers into allies starts with understanding their criteria.",
                evidence=original[:200],
                expected_outcome="Decision criteria identified.",
                priority="high", confidence=82,
                alternatives=["Would it help to prepare something for them?", "Should they join the next conversation?"],
                expires_when="Decision criteria understood",
                category="decision_maker", stage="decision_maker",
            )
        
        # Buying signal
        if any(w in text_lower for w in ["sounds good", "interesting", "next steps", "move forward"]):
            return CoachingRecommendation(
                semantic_key="buying_signal", title="Advance the conversation",
                action="Move toward concrete next step",
                suggested_wording="Based on what you've shared, I think it would be valuable to map this workflow and show you how this would work for your specific situation. Would next week work?",
                reason="Buying signals indicate readiness — don't keep discovering.",
                evidence=original[:200],
                expected_outcome="Concrete next step scheduled.",
                priority="high", confidence=85,
                alternatives=["Would it help to see how this works with your actual process?"],
                expires_when="Next step scheduled",
                category="buying_signal", stage="closing",
            )
        
        return None
    
    def _gap_question(self, gap: str) -> CoachingRecommendation | None:
        """Generate a question to fill a narrative gap."""
        if "cost unquantified" in gap:
            return CoachingRecommendation(
                semantic_key="gap_quantify", title="Quantify the impact",
                action="Ask about the cost of the problem",
                suggested_wording="What does that problem cost your team — in time, money, or delays — on a typical month?",
                reason="Quantified impact is the foundation of the business case.",
                evidence=gap,
                expected_outcome="Cost estimate that enables ROI comparison.",
                priority="high", confidence=78,
                category="narrative_gap", stage="pain_points",
            )
        if "urgency unclear" in gap:
            return _urgency_response(gap)
        if "decision process unknown" in gap:
            return CoachingRecommendation(
                semantic_key="gap_decision", title="Understand the decision process",
                action="Ask how decisions like this are made",
                suggested_wording="How does your organization typically evaluate and approve something like this?",
                reason="Knowing the decision process prevents late-stage surprises.",
                evidence=gap,
                expected_outcome="Clear decision process and stakeholders.",
                priority="high", confidence=78,
                category="narrative_gap", stage="decision_maker",
            )
        if "no next commitment" in gap or "no next step" in gap:
            close_rec = self._commitment_engine.determine(self._narrative_engine.narrative)
            if close_rec.commitment_type != "continue_discovery":
                return CoachingRecommendation(
                    semantic_key=f"close_{close_rec.commitment_type}",
                    title=close_rec.title,
                    action="Secure the next commitment",
                    suggested_wording=close_rec.suggested_wording,
                    reason=close_rec.reason,
                    evidence=gap,
                    expected_outcome="Next meeting or commitment secured.",
                    priority="critical",
                    confidence=close_rec.confidence,
                    category="closing", stage="closing",
                )
        return None
    
    def _dedup_and_return(self, result: CoachingRecommendation) -> CoachingRecommendation | None:
        """Check dedup and return if new."""
        if result.semantic_key in self._result_history[-5:]:
            return None
        self._result_history.append(result.semantic_key)
        if len(self._result_history) > 30:
            self._result_history = self._result_history[-30:]
        self._last_result = result
        return result
    
    def _detect_stage(self, text_lower: str):
        stage_keywords = {
            "rapport": ["how are you", "busy", "weekend", "weather"],
            "discovery": ["tell me about", "how do you", "what are you", "current", "process"],
            "pain_points": ["challenge", "problem", "issue", "struggling", "pain", "difficult", "frustrating"],
            "current_process": ["workflow", "currently", "steps", "how do you currently"],
            "budget": ["budget", "cost", "price", "pricing", "spend", "invest"],
            "timeline": ["timeline", "deadline", "when", "quarter", "urgent", "soon"],
            "decision_maker": ["decision", "approval", "boss", "manager", "sign off"],
            "solution": ["solution", "platform", "system", "would help", "could solve"],
            "closing": ["next steps", "follow up", "demo", "proposal", "trial", "start"],
        }
        for stage, keywords in stage_keywords.items():
            if any(kw in text_lower for kw in keywords):
                self._stage = stage
                break
    
    def get_state(self) -> dict:
        n = self._narrative_engine.narrative
        return {
            "stage": self._stage,
            "talk_ratio": round(self.talk_ratio, 2),
            "agent_words": self._agent_words,
            "prospect_words": self._prospect_words,
            "agent_utterances": self._agent_utterances,
            "prospect_utterances": self._prospect_utterances,
            "segments_processed": self._segment_count,
            "discovered": list(self._discovered),
            "both_channels_live": self._both_channels_live,
            "grace_period_active": self.in_grace_period,
            "last_prospect_text": self._last_prospect_text[:100] if self._last_prospect_text else "",
            "deal_narrative": n.to_dict(),
        }
    
    def get_last_result(self) -> CoachingRecommendation | None:
        return self._last_result
    
    def reset(self):
        self.__init__()
