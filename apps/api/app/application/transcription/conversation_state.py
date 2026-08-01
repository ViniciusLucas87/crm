"""
Sprint 47 — Conversation State & GPS Engine

Maintains an incremental conversation state object.
LLM never re-reads the entire transcript.
Only changed fields are updated.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any


@dataclass
class ConversationState:
    """Incremental state of the live sales conversation.
    
    Updated field-by-field as transcript flows in.
    Never serializes the full transcript for LLM calls.
    """
    
    # ── Conversation metadata ──
    call_id: str | None = None
    company_id: int | None = None
    
    # ── GPS / Stage ──
    current_stage: str = "opening"  # opening|rapport|discovery|pain|process|budget|timeline|solution|closing
    stage_confidence: int = 50
    destination_order: list[str] = field(default_factory=lambda: [
        "rapport", "discovery", "pain", "process", "budget", "timeline", 
        "authority", "solution", "closing"
    ])
    completed_stages: set[str] = field(default_factory=set)
    
    # ── Discovery (what we know) ──
    decision_maker: str = "unknown"       # unknown|partial|confirmed
    decision_maker_name: str = ""
    current_software: str = "unknown"
    current_software_name: str = ""
    pain_points: str = "unknown"
    pain_points_detail: str = ""
    budget: str = "unknown"
    budget_range: str = ""
    timeline: str = "unknown"
    timeline_detail: str = ""
    authority: str = "unknown"
    authority_detail: str = ""
    workflow: str = "unknown"
    workflow_detail: str = ""
    integrations: str = "unknown"
    integrations_detail: str = ""
    success_metrics: str = "unknown"
    success_metrics_detail: str = ""
    competitors: str = "unknown"
    competitors_detected: list[str] = field(default_factory=list)
    roi_discussed: bool = False
    
    # ── Buying signals ──
    buying_signals: list[dict] = field(default_factory=list)
    
    # ── Objections ──
    active_objections: list[dict] = field(default_factory=list)
    objections_resolved: int = 0
    
    # ── Conversation quality ──
    agent_words: int = 0
    customer_words: int = 0
    agent_utterances: int = 0
    customer_utterances: int = 0
    silence_count: int = 0
    interruptions: int = 0
    
    # ── Recommendations ──
    active_recommendation: dict | None = None  # ONE recommendation at a time
    recommendation_history: list[str] = field(default_factory=list)  # dedup keys
    
    # ── GPS route ──
    recommended_route: list[str] = field(default_factory=list)
    next_milestone: str = ""
    
    # ── Deal health ──
    discovery_quality: int = 0
    buying_intent: int = 0
    information_completeness: int = 0
    deal_risk: int = 50
    momentum: str = "neutral"
    close_probability: int = 0
    
    # ── Timestamps ──
    started_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    
    def touch(self):
        self.last_updated = datetime.now(UTC).isoformat()
    
    @property
    def talk_ratio(self) -> float:
        total = self.agent_words + self.customer_words
        return self.agent_words / total if total > 0 else 0.5
    
    @property
    def discovery_count(self) -> int:
        fields = [self.decision_maker, self.current_software, self.pain_points,
                  self.budget, self.timeline, self.authority, self.workflow,
                  self.integrations, self.success_metrics]
        return sum(1 for f in fields if f in ("partial", "confirmed"))
    
    @property
    def discovery_total(self) -> int:
        return 9
    
    def to_dict(self) -> dict:
        return {
            "current_stage": self.current_stage,
            "stage_confidence": self.stage_confidence,
            "completed_stages": list(self.completed_stages),
            "discovery": {
                "decision_maker": {"status": self.decision_maker, "detail": self.decision_maker_name},
                "current_software": {"status": self.current_software, "detail": self.current_software_name},
                "pain_points": {"status": self.pain_points, "detail": self.pain_points_detail},
                "budget": {"status": self.budget, "detail": self.budget_range},
                "timeline": {"status": self.timeline, "detail": self.timeline_detail},
                "authority": {"status": self.authority, "detail": self.authority_detail},
                "workflow": {"status": self.workflow, "detail": self.workflow_detail},
                "integrations": {"status": self.integrations, "detail": self.integrations_detail},
                "success_metrics": {"status": self.success_metrics, "detail": self.success_metrics_detail},
            },
            "competitors_detected": self.competitors_detected,
            "buying_signals": self.buying_signals[-10:],
            "active_objections": self.active_objections[-5:],
            "quality": {
                "talk_ratio": round(self.talk_ratio, 2),
                "agent_words": self.agent_words,
                "customer_words": self.customer_words,
                "silence_count": self.silence_count,
            },
            "active_recommendation": self.active_recommendation,
            "gps": {
                "destination_order": self.destination_order,
                "recommended_route": self.recommended_route,
                "next_milestone": self.next_milestone,
            },
            "deal_health": {
                "discovery_quality": self.discovery_quality,
                "buying_intent": self.buying_intent,
                "information_completeness": self.information_completeness,
                "deal_risk": self.deal_risk,
                "momentum": self.momentum,
                "close_probability": self.close_probability,
            },
            "discovery_count": self.discovery_count,
            "discovery_total": self.discovery_total,
        }


# ═══════════════════════════════════════════════════════════
# GPS ENGINE — calculates destination + route
# ═══════════════════════════════════════════════════════════

class GPSEngine:
    """Calculates the conversation GPS: where we are, where we're going, and the recommended route."""
    
    STAGE_LABELS = {
        "opening": "Open Conversation",
        "rapport": "Build Rapport", 
        "discovery": "Discovery",
        "pain": "Uncover Pain Points",
        "process": "Understand Process",
        "budget": "Discuss Budget",
        "timeline": "Establish Timeline",
        "authority": "Identify Decision Maker",
        "solution": "Present Solution",
        "closing": "Close & Next Steps",
    }
    
    STAGE_QUESTIONS = {
        "rapport": "How has business been this quarter?",
        "discovery": "Can you walk me through your current process?",
        "pain": "What's the biggest challenge your team faces?",
        "process": "What happens after [key step] in your workflow?",
        "budget": "Have you allocated budget for solving this?",
        "timeline": "What's your timeline for making a decision?",
        "authority": "Who else would need to be involved?",
        "solution": "Would you like to see how this works for your use case?",
        "closing": "What would you need to feel confident moving forward?",
    }
    
    def calculate(self, state: ConversationState) -> dict:
        """Generate GPS data from conversation state."""
        # Current destination (next uncompleted stage)
        destination = None
        for stage in state.destination_order:
            if stage not in state.completed_stages:
                destination = stage
                break
        
        # Build recommended route (next 3 stages)
        route = []
        for stage in state.destination_order:
            if stage not in state.completed_stages:
                route.append(self.STAGE_QUESTIONS.get(stage, f"Explore {stage}"))
            if len(route) >= 3:
                break
        
        # Next milestone
        next_milestone = destination or "closing"
        
        # Progress
        completed = len(state.completed_stages)
        total = len(state.destination_order)
        
        return {
            "current_destination": self.STAGE_LABELS.get(destination, "Complete"),
            "destination_key": destination or "closing",
            "next_milestone": self.STAGE_LABELS.get(next_milestone, ""),
            "recommended_route": route,
            "progress_pct": int(completed / total * 100) if total > 0 else 0,
            "completed_count": completed,
            "total_count": total,
            "stages": [
                {
                    "key": s,
                    "label": self.STAGE_LABELS.get(s, s),
                    "status": "completed" if s in state.completed_stages else 
                              "current" if s == destination else "pending"
                }
                for s in state.destination_order
            ],
        }


# ═══════════════════════════════════════════════════════════
# SMART PRIORITY ENGINE — one recommendation, never duplicate
# ═══════════════════════════════════════════════════════════

class PriorityEngine:
    """Ensures only ONE recommendation is active. Never duplicates. Manages lifecycle."""
    
    def evaluate(self, state: ConversationState) -> dict | None:
        """Return the single highest-priority recommendation, or None."""
        candidates = []
        
        # 1. Talk ratio too high — CRITICAL
        if state.talk_ratio > 0.70:
            candidates.append({
                "priority": "critical",
                "key": "talk_ratio_high",
                "title": "Let the customer speak",
                "detail": f"You've spoken {int(state.talk_ratio*100)}% of the time. Ask an open question.",
                "action": "Ask: 'Can you tell me more about that?'",
                "confidence": 95,
            })
        
        # 2. Missing decision maker — HIGH
        if state.decision_maker == "unknown" and state.discovery_count >= 3:
            candidates.append({
                "priority": "high",
                "key": "missing_decision_maker",
                "title": "Identify the decision maker",
                "detail": "You haven't identified who approves purchases.",
                "action": "Ask: 'Who else would be involved in evaluating this?'",
                "confidence": 85,
            })
        
        # 3. Multiple buying signals, haven't pitched — HIGH
        if len(state.buying_signals) >= 2 and "solution" not in state.completed_stages:
            candidates.append({
                "priority": "high",
                "key": "ready_to_pitch",
                "title": "Strong interest — transition to solution",
                "detail": f"{len(state.buying_signals)} buying signals detected. Present your solution.",
                "action": "Say: 'Based on what you've shared, I think we can help with...'",
                "confidence": 80,
            })
        
        # 4. Budget not discussed after pain points — HIGH
        if state.budget == "unknown" and state.pain_points in ("partial", "confirmed"):
            candidates.append({
                "priority": "high",
                "key": "missing_budget",
                "title": "Discuss budget",
                "detail": "Pain points confirmed but budget not explored.",
                "action": "Ask: 'Have you allocated budget for solving this problem?'",
                "confidence": 80,
            })
        
        # 5. Timeline missing after budget — MEDIUM
        if state.timeline == "unknown" and state.budget in ("partial", "confirmed"):
            candidates.append({
                "priority": "medium",
                "key": "missing_timeline",
                "title": "Establish timeline",
                "detail": "Budget discussed but no timeline established.",
                "action": "Ask: 'What's your timeline for making a decision?'",
                "confidence": 75,
            })
        
        # 6. No pain points yet — MEDIUM
        if state.pain_points == "unknown" and state.discovery_count >= 2:
            candidates.append({
                "priority": "medium", 
                "key": "missing_pain",
                "title": "Uncover pain points",
                "detail": "You've covered basics but haven't found specific pain.",
                "action": "Ask: 'What's the most frustrating part of your current process?'",
                "confidence": 70,
            })
        
        # 7. Good momentum — encourage close — LOW
        if len(state.buying_signals) >= 3 and state.discovery_count >= 6:
            candidates.append({
                "priority": "low",
                "key": "close_opportunity",
                "title": "Strong position — consider closing",
                "detail": "Excellent discovery and multiple signals. Time to discuss next steps.",
                "action": "Say: 'Would it make sense to schedule a follow-up to discuss specifics?'",
                "confidence": 70,
            })
        
        if not candidates:
            return None
        
        # Sort by priority (critical > high > medium > low), then by confidence
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        candidates.sort(key=lambda c: (priority_order.get(c["priority"], 99), -c["confidence"]))
        
        best = candidates[0]
        
        # Dedup: check if we've already shown this
        if best["key"] in state.recommendation_history[-5:]:
            return None
        
        state.recommendation_history.append(best["key"])
        state.active_recommendation = best
        return best


# ═══════════════════════════════════════════════════════════
# COMPETITIVE INTELLIGENCE
# ═══════════════════════════════════════════════════════════

COMPETITOR_INTEL = {
    "salesforce": {
        "strengths": "Market leader, extensive ecosystem",
        "weaknesses": "Expensive, complex, slow implementation",
        "positioning": "We're faster to deploy and more affordable for mid-market",
        "migration": "Data export available, API migration possible",
    },
    "hubspot": {
        "strengths": "Great marketing tools, freemium model",
        "weaknesses": "Limited customization, expensive at scale",
        "positioning": "We offer deeper industry-specific workflows",
        "migration": "CSV export available, gradual transition possible",
    },
    "zoho": {
        "strengths": "Affordable, broad suite",
        "weaknesses": "Limited support, clunky UI",
        "positioning": "We provide dedicated support and a modern interface",
        "migration": "API access available for data transfer",
    },
    "quickbooks": {
        "strengths": "Accounting standard, widely used",
        "weaknesses": "Limited CRM/operations features",
        "positioning": "We complement QuickBooks with operational workflow",
        "migration": "Integrates with QuickBooks via API",
    },
    "procore": {
        "strengths": "Construction-specific, compliance features",
        "weaknesses": "Expensive, steep learning curve",
        "positioning": "We're more flexible and affordable for growing firms",
        "migration": "Data export available",
    },
    "jobber": {
        "strengths": "Field service focused, scheduling",
        "weaknesses": "Limited reporting, no advanced workflow",
        "positioning": "We offer deeper process automation and analytics",
        "migration": "CSV import supported",
    },
    "buildertrend": {
        "strengths": "Construction project management",
        "weaknesses": "Limited customization, dated interface",
        "positioning": "We offer modern UI with flexible workflows",
        "migration": "Data export tools available",
    },
    "servicetitan": {
        "strengths": "HVAC/plumbing focused, dispatching",
        "weaknesses": "Very expensive, industry-locked",
        "positioning": "Cross-industry flexibility at better value",
        "migration": "API access available",
    },
}


def detect_competitor(text: str) -> dict | None:
    """Detect competitor mentions and return intelligence."""
    text_lower = text.lower()
    for name, intel in COMPETITOR_INTEL.items():
        if name in text_lower:
            return {"name": name.title(), **intel, "evidence": text[:150]}
    return None
