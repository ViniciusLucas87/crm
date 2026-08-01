"""
Sprint 47.5 — Next Best Question Engine

Generates specific, contextual follow-up questions based on:
- Last prospect statement
- Current conversation stage
- Company context (industry, role)
- Discovered facts
- Missing discovery fields
- Active objections / buying signals

Produces: primary question + 2-4 alternatives + why it matters + transition
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any


@dataclass 
class QuestionRecommendation:
    """A recommended question with alternatives and context."""
    primary: str                              # The single best question to ask
    alternatives: list[str] = field(default_factory=list)  # 2-4 alternatives
    question_type: str = "clarification"      # clarification | workflow | impact | ownership | frequency | cost | risk | decision_maker | budget | timeline | success_criteria | next_step
    why_it_matters: str = ""
    expected_discovery_value: str = ""
    transition_phrase: str = ""
    confidence: int = 75
    source_trigger: str = ""                  # What triggered this recommendation


class NextBestQuestionEngine:
    """Generates the next best question based on conversation context."""
    
    def __init__(self):
        self._asked_questions: list[str] = []  # To avoid repeats
        self._company_context: dict = {}
    
    def set_company_context(self, ctx: dict):
        """Set company/contact context for industry-specific questions."""
        self._company_context = ctx
    
    def generate(
        self,
        last_prospect_text: str,
        stage: str,
        discovered_facts: dict,
        missing_discovery: list[str],
    ) -> QuestionRecommendation | None:
        """Generate the next best question."""
        
        # ── If prospect just said something specific, ladder from it ──
        if last_prospect_text.strip():
            ladder = self._build_question_ladder(last_prospect_text, stage)
            if ladder:
                return ladder
        
        # ── Stage-based fallback ──
        return self._stage_question(stage, missing_discovery)
    
    def _build_question_ladder(self, text: str, stage: str) -> QuestionRecommendation | None:
        """Build a question ladder from the prospect's last statement."""
        text_lower = text.lower()
        
        # Detect what the prospect revealed
        triggers = []
        
        if any(w in text_lower for w in ["paper", "form", "print", "handwritten"]):
            triggers.append(("paper", self._paper_ladder()))
        if any(w in text_lower for w in ["spreadsheet", "excel", "sheets"]):
            triggers.append(("spreadsheet", self._spreadsheet_ladder()))
        if any(w in text_lower for w in ["manually", "data entry", "by hand"]):
            triggers.append(("manual", self._manual_ladder()))
        if any(w in text_lower for w in ["problem", "challenge", "issue", "struggling", "pain"]):
            triggers.append(("pain", self._pain_ladder()))
        if any(w in text_lower for w in ["expensive", "cost", "price", "budget", "afford"]):
            triggers.append(("cost", self._cost_ladder()))
        if any(w in text_lower for w in ["timeline", "deadline", "soon", "urgent"]):
            triggers.append(("timeline", self._timeline_ladder()))
        if any(w in text_lower for w in ["software", "system", "platform", "tool", "using"]):
            triggers.append(("current_solution", self._current_solution_ladder()))
        if any(w in text_lower for w in ["approval", "boss", "manager", "decision"]):
            triggers.append(("decision_maker", self._decision_maker_ladder()))
        
        if not triggers:
            return None
        
        # Pick highest priority trigger
        priority_order = ["paper", "spreadsheet", "manual", "pain", "cost", "timeline", "current_solution", "decision_maker"]
        for key in priority_order:
            for t_key, ladder in triggers:
                if t_key == key:
                    return ladder
        
        return triggers[0][1]
    
    def _paper_ladder(self) -> QuestionRecommendation:
        alts = [
            "What information from those paper forms has to be entered manually afterward?",
            "Who handles the paper forms after they're completed?",
            "How long does it typically take to process each form?",
            "Where do errors or delays usually happen in that handoff?",
        ]
        return QuestionRecommendation(
            primary=alts[0],
            alternatives=alts[1:],
            question_type="workflow",
            why_it_matters="Reveals duplicate data entry, handoff ownership, and measurable labour cost.",
            expected_discovery_value="Quantify manual processing time and identify automation opportunity.",
            transition_phrase="That helps me understand where the bottlenecks are.",
            confidence=88,
            source_trigger="paper_mention",
        )
    
    def _spreadsheet_ladder(self) -> QuestionRecommendation:
        alts = [
            "How does the data get from the field into the spreadsheet?",
            "Who updates the spreadsheet and how often?",
            "What happens when multiple people need to access or update it at the same time?",
            "How do you generate reports or share information from that spreadsheet?",
        ]
        return QuestionRecommendation(
            primary=alts[0],
            alternatives=alts[1:],
            question_type="workflow",
            why_it_matters="Exposes the manual data transfer step between operations and administration.",
            expected_discovery_value="Identify where field data becomes administrative work.",
            transition_phrase="That shows me where the process could be streamlined.",
            confidence=88,
            source_trigger="spreadsheet_mention",
        )
    
    def _manual_ladder(self) -> QuestionRecommendation:
        alts = [
            "Which part of that manual process takes the most time?",
            "How many people are involved in that workflow from start to finish?",
            "What would change first if that step were automated?",
            "How often do mistakes or delays come from the manual steps?",
        ]
        return QuestionRecommendation(
            primary=alts[0],
            alternatives=alts[1:],
            question_type="impact",
            why_it_matters="Quantifies the operational cost of the manual bottleneck.",
            expected_discovery_value="Build the business case for automation by measuring current cost.",
            transition_phrase="That gives us a clear target for improvement.",
            confidence=85,
            source_trigger="manual_mention",
        )
    
    def _pain_ladder(self) -> QuestionRecommendation:
        alts = [
            "How often does that problem occur, and who is affected?",
            "What have you tried so far to address it?",
            "What would solving this mean for your team's daily work?",
            "Is this the biggest bottleneck or are there others?",
        ]
        return QuestionRecommendation(
            primary=alts[0],
            alternatives=alts[1:],
            question_type="impact",
            why_it_matters="Moves from identifying pain to quantifying its frequency and scope.",
            expected_discovery_value="Understand frequency, impact, and prioritization.",
            transition_phrase="That helps me understand the full picture.",
            confidence=85,
            source_trigger="pain_mention",
        )
    
    def _cost_ladder(self) -> QuestionRecommendation:
        alts = [
            "What does the current process cost in staff time before we discuss any implementation price?",
            "What budget range have you considered for solving this?",
            "How do you typically evaluate the ROI on operational improvements?",
            "Is there already budget allocated or would this need approval?",
        ]
        return QuestionRecommendation(
            primary=alts[0],
            alternatives=alts[1:],
            question_type="cost",
            why_it_matters="Shifts conversation from price objection to value comparison.",
            expected_discovery_value="Reframe cost as investment and understand budget process.",
            transition_phrase="That gives us a baseline to compare against.",
            confidence=85,
            source_trigger="cost_mention",
        )
    
    def _timeline_ladder(self) -> QuestionRecommendation:
        alts = [
            "What's driving that timeline on your end?",
            "What happens if you don't have a solution in place by then?",
            "Is there a specific event or deadline you're working toward?",
            "Would a phased approach work within that timeline?",
        ]
        return QuestionRecommendation(
            primary=alts[0],
            alternatives=alts[1:],
            question_type="timeline",
            why_it_matters="Reveals urgency drivers and consequences of delay.",
            expected_discovery_value="Understand real deadline vs. aspirational timeline.",
            transition_phrase="That helps us plan the right approach.",
            confidence=85,
            source_trigger="timeline_mention",
        )
    
    def _current_solution_ladder(self) -> QuestionRecommendation:
        alts = [
            "What's one thing your current system doesn't do that you wish it did?",
            "How long have you been using it, and what made you choose it originally?",
            "What happens when you need to do something the system doesn't support?",
            "Are there workarounds your team has developed to fill the gaps?",
        ]
        return QuestionRecommendation(
            primary=alts[0],
            alternatives=alts[1:],
            question_type="clarification",
            why_it_matters="Identifies the gap between current solution and real needs.",
            expected_discovery_value="Understand pain points with current solution and buying motivation.",
            transition_phrase="That helps me understand where the gap really is.",
            confidence=83,
            source_trigger="current_solution_mention",
        )
    
    def _decision_maker_ladder(self) -> QuestionRecommendation:
        alts = [
            "What would they need to see to feel confident moving forward?",
            "Would it help if I prepared a summary specifically for them?",
            "What typically matters most to them in a decision like this?",
            "Should we include them in the next conversation?",
        ]
        return QuestionRecommendation(
            primary=alts[0],
            alternatives=alts[1:],
            question_type="decision_maker",
            why_it_matters="Turns the decision-maker into an ally rather than a blocker.",
            expected_discovery_value="Understand approval criteria and engage stakeholders early.",
            transition_phrase="That way we make sure everyone has what they need.",
            confidence=82,
            source_trigger="decision_maker_mention",
        )
    
    def _stage_question(self, stage: str, missing: list[str]) -> QuestionRecommendation | None:
        """Fallback: stage-appropriate question when no specific trigger."""
        stage_questions = {
            "opening": QuestionRecommendation(
                primary="Before we dive in, could you tell me a bit about your role and what you're hoping to accomplish today?",
                alternatives=["What prompted you to explore this now?", "What's top of mind for your team at the moment?"],
                question_type="clarification",
                why_it_matters="Establishes the prospect's context, role, and motivation.",
                expected_discovery_value="Understand who we're speaking with and why now.",
                transition_phrase="That gives me useful context. Let me share what I'd like to cover today.",
                confidence=80,
                source_trigger="stage_opening",
            ),
            "rapport": QuestionRecommendation(
                primary="How has business been for your team recently?",
                alternatives=["What's been keeping your team busy lately?", "Any recent changes in how your team operates?"],
                question_type="clarification",
                why_it_matters="Builds connection while revealing operational context.",
                expected_discovery_value="Understand current business climate and priorities.",
                transition_phrase="That's helpful. Could you walk me through how that process works today?",
                confidence=78,
                source_trigger="stage_rapport",
            ),
            "discovery": QuestionRecommendation(
                primary="Can you walk me through how you handle that process currently, from start to finish?",
                alternatives=["What does a typical day look like for the team involved?", "How did the current process come together?"],
                question_type="workflow",
                why_it_matters="Maps the actual workflow before suggesting improvements.",
                expected_discovery_value="Complete process map with roles, steps, and handoffs.",
                transition_phrase="That gives me a clear picture. Where does that process create the most friction?",
                confidence=82,
                source_trigger="stage_discovery",
            ),
            "pain_points": QuestionRecommendation(
                primary="What's the most time-consuming or frustrating part of that process?",
                alternatives=["Where do you see the most mistakes or delays?", "What would your team say is the biggest bottleneck?"],
                question_type="impact",
                why_it_matters="Identifies the specific pain that justifies change.",
                expected_discovery_value="Quantified pain point with owner and impact.",
                transition_phrase="That's exactly the kind of problem we help solve.",
                confidence=83,
                source_trigger="stage_pain",
            ),
        }
        
        q = stage_questions.get(stage)
        if q:
            # Don't repeat recently asked questions
            if q.primary in self._asked_questions:
                return None
            self._asked_questions.append(q.primary)
            if len(self._asked_questions) > 10:
                self._asked_questions = self._asked_questions[-10:]
            return q
        
        return None
