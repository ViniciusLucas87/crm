"""
Sprint 47.7 — Deal Narrative Engine

Maintains a live, evolving DealNarrative for every call.
Every coaching recommendation must contribute to this narrative.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DealNarrative:
    """Live deal narrative that evolves as the prospect speaks."""
    
    # ── Situation ──
    opening_context: str = ""
    current_situation: str = ""           # What they do today
    operational_problem: str = ""         # The friction
    root_cause: str = ""                  # Why it happens
    affected_people: str = ""             # Who is affected
    
    # ── Impact ──
    business_impact: str = ""             # What it costs them
    quantified_cost: str = ""             # Specific number if mentioned
    urgency: str = "unknown"              # unknown | low | medium | high
    
    # ── Solution ──
    desired_outcome: str = ""             # What they want
    solution_hypothesis: str = ""         # How PNS might help
    pns_value_position: str = ""          # Why PNS specifically
    
    # ── Evidence ──
    supporting_evidence: list[str] = field(default_factory=list)
    
    # ── Commercial ──
    objections: list[str] = field(default_factory=list)
    decision_process: str = "unknown"
    decision_makers: list[str] = field(default_factory=list)
    next_commitment: str = ""             # What we need next
    close_readiness: str = "not_ready"    # not_ready | developing | next_meeting | technical_discovery | proposal | commercial_close
    
    # ── Gaps ──
    narrative_gaps: list[str] = field(default_factory=list)
    
    # ── Momentum ──
    momentum: str = "stable"              # increasing | stable | declining | stalled
    micro_commitments: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "current_situation": self.current_situation,
            "operational_problem": self.operational_problem,
            "business_impact": self.business_impact,
            "quantified_cost": self.quantified_cost,
            "urgency": self.urgency,
            "desired_outcome": self.desired_outcome,
            "solution_hypothesis": self.solution_hypothesis,
            "pns_value_position": self.pns_value_position,
            "objections": self.objections,
            "decision_process": self.decision_process,
            "decision_makers": self.decision_makers,
            "next_commitment": self.next_commitment,
            "close_readiness": self.close_readiness,
            "narrative_gaps": self.narrative_gaps,
            "momentum": self.momentum,
            "micro_commitments": self.micro_commitments,
        }


class DealNarrativeEngine:
    """Builds and updates the DealNarrative from prospect statements."""
    
    def __init__(self):
        self._narrative = DealNarrative()
    
    @property
    def narrative(self) -> DealNarrative:
        return self._narrative
    
    def update_from_segment(self, text: str, is_prospect: bool):
        """Update the narrative from a new transcript segment."""
        if not is_prospect:
            return
        t = text.lower()
        
        # Current situation
        if any(w in t for w in ["we use", "currently", "our process", "we handle"]):
            self._update_field("current_situation", text[:200])
        
        # Problem / pain
        if any(w in t for w in ["problem", "challenge", "issue", "struggling", "pain", "headache", "frustrating", "difficult", "hard to"]):
            self._update_field("operational_problem", text[:200])
            self._detect_impact()
        
        # Root cause
        if any(w in t for w in ["because", "due to", "since we", "the reason"]):
            self._update_field("root_cause", text[:200])
        
        # People affected
        if any(w in t for w in ["team", "staff", "administrator", "manager", "field", "office", "department"]):
            if not self._narrative.affected_people:
                self._narrative.affected_people = text[:200]
        
        # Quantified cost
        self._detect_cost(text)
        
        # Desired outcome
        if any(w in t for w in ["we want", "we need", "we'd like", "ideally", "looking for", "hope to"]):
            self._update_field("desired_outcome", text[:200])
        
        # Urgency
        if any(w in t for w in ["urgent", "asap", "immediately", "this quarter", "this month", "soon", "can't wait"]):
            self._narrative.urgency = "high"
        elif any(w in t for w in ["next quarter", "this year", "eventually", "sometime"]):
            if self._narrative.urgency in ("unknown", "low"):
                self._narrative.urgency = "medium"
        
        # Decision makers
        if any(w in t for w in ["ceo", "cto", "cfo", "vp", "director", "my boss", "approval", "sign off"]):
            if not self._narrative.decision_process:
                self._narrative.decision_process = "identified"
        
        # Update gaps
        self._update_gaps()
        self._update_momentum()
        self._update_close_readiness()
    
    def _detect_cost(self, text: str):
        """Detect and extract quantified cost mentions."""
        import re
        # Pattern: $X,XXX per month / per year / etc.
        cost_patterns = [
            r'\$\s*(\d[\d,]*)\s*(per|a)\s*(month|year|week|day)',
            r'(\d[\d,]*)\s*(thousand|million)?\s*dollars?\s*(per|a)\s*(month|year|week)',
            r'cost(?:s|ing)?\s*(?:us|about|around|roughly)?\s*\$?\s*(\d[\d,]*)',
        ]
        for pattern in cost_patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                self._narrative.quantified_cost = text[:200]
                self._narrative.business_impact = text[:200]
                return
    
    def _detect_impact(self):
        """Set business impact from operational problem if new."""
        if not self._narrative.business_impact and self._narrative.operational_problem:
            self._narrative.business_impact = self._narrative.operational_problem
    
    def _update_field(self, field: str, value: str):
        """Update a narrative field, appending if it already has content."""
        current = getattr(self._narrative, field, "")
        if not current:
            setattr(self._narrative, field, value)
        elif len(current) < 500:
            setattr(self._narrative, field, current + " | " + value[:200])
    
    def _update_gaps(self):
        """Identify narrative gaps."""
        n = self._narrative
        gaps = []
        
        if not n.operational_problem:
            gaps.append("No operational problem identified")
        elif not n.business_impact:
            gaps.append("Pain detected but impact unknown")
        elif not n.quantified_cost:
            gaps.append("Impact known but cost unquantified")
        elif n.urgency == "unknown":
            gaps.append("Cost known but urgency unclear")
        
        if n.operational_problem and not n.solution_hypothesis:
            gaps.append("Problem identified but no solution hypothesis")
        
        if n.quantified_cost and n.urgency != "unknown" and n.decision_process == "unknown":
            gaps.append("Strong case but decision process unknown")
        
        if n.solution_hypothesis and not n.next_commitment:
            gaps.append("Solution fit but no next commitment")
        
        if len(n.micro_commitments) >= 2 and not n.next_commitment:
            gaps.append("Multiple micro-commitments but no next step requested")
        
        n.narrative_gaps = gaps
    
    def _update_momentum(self):
        """Track deal momentum."""
        n = self._narrative
        signals_up = 0
        signals_down = 0
        
        if n.quantified_cost: signals_up += 1
        if n.urgency in ("medium", "high"): signals_up += 1
        if n.decision_process != "unknown": signals_up += 1
        if n.next_commitment: signals_up += 1
        if len(n.micro_commitments) >= 3: signals_up += 1
        if n.solution_hypothesis: signals_up += 1
        
        if n.objections: signals_down += len(n.objections)
        if n.urgency == "low": signals_down += 1
        if len(n.narrative_gaps) >= 4: signals_down += 1
        
        score = signals_up - signals_down
        if score >= 3:
            n.momentum = "increasing"
        elif score >= 1:
            n.momentum = "stable"
        elif score >= -1:
            n.momentum = "declining"
        else:
            n.momentum = "stalled"
    
    def _update_close_readiness(self):
        """Calculate close readiness score."""
        n = self._narrative
        score = 0
        max_score = 10
        
        if n.operational_problem: score += 1      # pain clarity
        if n.quantified_cost: score += 2           # quantified impact (weighted)
        if n.urgency != "unknown": score += 1      # urgency
        if n.solution_hypothesis: score += 1       # solution fit
        if n.decision_process != "unknown": score += 1   # decision maker
        if n.urgency in ("medium", "high"): score += 1   # budget/timeline indication
        if n.desired_outcome: score += 1           # desired future state
        if not n.objections: score += 1            # no active objections
        if n.next_commitment: score += 1           # next step willingness
        
        pct = int(score / max_score * 100)
        
        if pct >= 85:
            n.close_readiness = "commercial_close"
        elif pct >= 70:
            n.close_readiness = "proposal"
        elif pct >= 55:
            n.close_readiness = "technical_discovery"
        elif pct >= 40:
            n.close_readiness = "next_meeting"
        elif pct >= 20:
            n.close_readiness = "developing"
        else:
            n.close_readiness = "not_ready"
    
    def add_micro_commitment(self, commitment: str):
        """Track a micro-commitment from the prospect."""
        n = self._narrative
        if commitment not in n.micro_commitments:
            n.micro_commitments.append(commitment)
            n.momentum = "increasing"
    
    def add_objection(self, objection: str):
        n = self._narrative
        if objection not in n.objections:
            n.objections.append(objection)
    
    def set_solution_hypothesis(self, hypothesis: str):
        n = self._narrative
        n.solution_hypothesis = hypothesis
        n.pns_value_position = f"Custom workflow automation built around {hypothesis[:100]}"
    
    def reset(self):
        self._narrative = DealNarrative()
