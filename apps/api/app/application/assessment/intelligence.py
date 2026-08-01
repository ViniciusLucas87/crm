"""
Sprint 47.9 — Assessment Intelligence Service

Deterministic, rule-based intelligence engine for automation assessments.
No LLM dependency. Produces structured intelligence from raw answers.

Outputs:
  - primary pain point
  - recommended PNS solutions with reasons
  - discovery questions
  - next sales action
  - urgency / buying signals
  - project size band
  - likely decision-maker role
  - structured intelligence dict for persistence
  - email view model (internal + visitor)
"""

from __future__ import annotations

import logging
from datetime import datetime, UTC
from typing import Any

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════
# RULE ENGINE — Problem → Solution Mappings
# ═══════════════════════════════════════════════════════════

PROBLEM_SOLUTION_MAP: dict[str, dict[str, Any]] = {
    "Repetitive data entry": {
        "category": "Workflow Automation",
        "reason": "Prospect identified repetitive manual data entry as a key problem — automation can eliminate re-keying.",
        "confidence": 0.92,
    },
    "Reporting": {
        "category": "Dashboard and Reporting System",
        "reason": "Prospect struggles with reporting — automated dashboards and scheduled reports replace manual compilation.",
        "confidence": 0.88,
    },
    "Managing documents": {
        "category": "AI Document Assistant",
        "reason": "Document management is a bottleneck — AI document processing and automated classification reduce manual handling.",
        "confidence": 0.85,
    },
    "Scheduling and dispatching": {
        "category": "Scheduling and Dispatch Platform",
        "reason": "Scheduling/dispatching challenges indicate need for an automated coordination system.",
        "confidence": 0.90,
    },
    "Customer communication": {
        "category": "Custom CRM and Follow-up Automation",
        "reason": "Customer communication gaps suggest a CRM with automated follow-up workflows.",
        "confidence": 0.87,
    },
    "Inventory tracking": {
        "category": "Custom Business Application",
        "reason": "Inventory tracking issues point to a need for a custom inventory management application.",
        "confidence": 0.82,
    },
    "Invoicing and billing": {
        "category": "Workflow Automation",
        "reason": "Invoicing pain indicates a need for automated billing and payment processing.",
        "confidence": 0.84,
    },
    "Compliance and safety": {
        "category": "Inspection and Reporting System",
        "reason": "Compliance/safety concerns suggest mobile inspection tools with automated evidence collection.",
        "confidence": 0.86,
    },
    "System integration": {
        "category": "Systems Integration",
        "reason": "Disconnected systems indicate a need for integration middleware and unified operations dashboard.",
        "confidence": 0.89,
    },
    "Quality control": {
        "category": "Inspection and Reporting System",
        "reason": "Quality control challenges suggest mobile QC with automated reporting and alerts.",
        "confidence": 0.83,
    },
    "Approvals": {
        "category": "Workflow Automation",
        "reason": "Approval bottlenecks indicate a need for automated approval workflows with digital audit trails.",
        "confidence": 0.85,
    },
}

PROCESS_SOLUTION_MAP: dict[str, dict[str, Any]] = {
    "Paper forms": {
        "category": "Inspection and Reporting System",
        "reason": "Paper forms create re-entry work and delays — mobile digital forms eliminate double-handling.",
        "confidence": 0.94,
    },
    "Spreadsheets": {
        "category": "Workflow Automation",
        "reason": "Spreadsheet-based processes are error-prone and don't scale — custom business applications replace them.",
        "confidence": 0.91,
    },
    "Multiple software tools": {
        "category": "Systems Integration",
        "reason": "Information spread across multiple tools creates data silos — integration centralizes operations.",
        "confidence": 0.90,
    },
    "Manual processes": {
        "category": "Custom Business Application",
        "reason": "Fully manual workflows indicate a greenfield opportunity for a purpose-built business application.",
        "confidence": 0.88,
    },
    "Email": {
        "category": "Custom CRM",
        "reason": "Email-based workflows lack tracking and automation — a CRM with workflow automation replaces ad-hoc email.",
        "confidence": 0.85,
    },
    "Phone calls": {
        "category": "Scheduling and Dispatch Platform",
        "reason": "Phone-based coordination is inefficient — dispatch and scheduling software streamlines field operations.",
        "confidence": 0.80,
    },
}

INDUSTRY_SOLUTION_MAP: dict[str, dict[str, Any]] = {
    "Construction / Trades": {
        "category": "Inspection and Reporting System",
        "reason": "Construction companies benefit from mobile inspection, site reporting, and automated compliance.",
        "confidence": 0.90,
    },
    "Property Management": {
        "category": "Scheduling and Dispatch Platform",
        "reason": "Property managers need automated maintenance scheduling, tenant communication, and inspection tracking.",
        "confidence": 0.88,
    },
    "Manufacturing": {
        "category": "Workflow Automation",
        "reason": "Manufacturers benefit from production workflow automation, quality tracking, and inventory integration.",
        "confidence": 0.87,
    },
    "Tourism / Transportation": {
        "category": "Scheduling and Dispatch Platform",
        "reason": "Tourism/transportation operators need booking, dispatch, and fleet management automation.",
        "confidence": 0.85,
    },
}

TIME_BAND_URGENCY: dict[str, dict[str, str]] = {
    "More than 40 hours": {"urgency": "critical", "message": "Over 40 hours/week lost — immediate action required."},
    "20-40 hours": {"urgency": "high", "message": "20-40 hours/week represents a full-time equivalent — strong urgency."},
    "20–40 hours": {"urgency": "high", "message": "20-40 hours/week represents a full-time equivalent — strong urgency."},
    "10-20 hours": {"urgency": "medium", "message": "10-20 hours/week is significant — good automation candidate."},
    "10–20 hours": {"urgency": "medium", "message": "10-20 hours/week is significant — good automation candidate."},
    "5-10 hours": {"urgency": "medium", "message": "5-10 hours/week — worthwhile automation opportunity."},
    "5–10 hours": {"urgency": "medium", "message": "5-10 hours/week — worthwhile automation opportunity."},
    "Less than 5 hours": {"urgency": "low", "message": "Under 5 hours/week — monitoring for growth potential."},
}

PEOPLE_BAND_SIZE: dict[str, str] = {
    "50+": "enterprise",
    "16-50": "large",
    "6-15": "medium",
    "2-5": "small",
    "1": "micro",
}


# ═══════════════════════════════════════════════════════════
# DISCOVERY QUESTION TEMPLATES
# ═══════════════════════════════════════════════════════════

DISCOVERY_QUESTIONS_BY_PROBLEM: dict[str, list[str]] = {
    "Repetitive data entry": [
        "What information is being entered repeatedly, and where does it originate?",
        "How many people spend time on data entry each week?",
        "What happens to the data after it is entered — who consumes it?",
    ],
    "Reporting": [
        "What reports do you produce regularly, and who needs them?",
        "How long does it currently take to compile each report?",
        "What decisions depend on these reports being accurate and timely?",
    ],
    "Managing documents": [
        "What types of documents are you managing, and how are they stored today?",
        "Who needs access to these documents, and how do they find them?",
        "Are there compliance or retention requirements for these documents?",
    ],
    "Scheduling and dispatching": [
        "How do you currently schedule jobs and dispatch your team?",
        "What happens when a schedule changes mid-day — how is the team notified?",
        "How much time does the dispatcher or manager spend on scheduling each week?",
    ],
    "Customer communication": [
        "How do you currently track customer interactions and follow-ups?",
        "What communication channels do your customers expect?",
        "How do you ensure nothing falls through the cracks after a conversation?",
    ],
    "Inventory tracking": [
        "How do you currently know what inventory you have and where it is?",
        "How often do stockouts or over-ordering cause problems?",
        "Who is responsible for inventory accuracy today?",
    ],
    "Invoicing and billing": [
        "What does your current invoicing process look like from job completion to payment?",
        "How long does it typically take to get paid after work is completed?",
        "How many invoices do you process each month?",
    ],
    "Compliance and safety": [
        "What compliance or safety documentation are you required to maintain?",
        "How do you currently collect and store safety evidence?",
        "What would happen during an audit with your current system?",
    ],
    "System integration": [
        "Which software tools does your team use daily, and do they talk to each other?",
        "Where do you see the biggest gap between systems?",
        "How much time is spent moving data between different tools?",
    ],
    "Quality control": [
        "What does your quality control process look like today?",
        "How are defects or issues tracked and resolved?",
        "How do you know if quality is improving or declining over time?",
    ],
    "Approvals": [
        "What types of approvals are required in your workflow?",
        "How long do approvals typically take, and where do they get stuck?",
        "What is the cost of an approval delay to your business?",
    ],
}

DISCOVERY_QUESTIONS_BY_PROCESS: dict[str, list[str]] = {
    "Paper forms": [
        "What happens to paper forms after they are completed in the field?",
        "Who transcribes or enters the data, and how long does that take?",
        "Where do errors or delays usually creep in with paper-based workflows?",
    ],
    "Spreadsheets": [
        "How many spreadsheets are in active use, and who maintains them?",
        "How do you handle version control and avoid conflicting edits?",
        "What would break if the main spreadsheet became corrupted tomorrow?",
    ],
    "Multiple software tools": [
        "Which tools contain the 'source of truth' for different parts of your operation?",
        "How do you currently reconcile information across different systems?",
        "What's the cost of having information scattered — in time, errors, or missed opportunities?",
    ],
    "Manual processes": [
        "Walk me through a typical day — where does most of the manual work happen?",
        "If you could automate one process tomorrow, which would have the biggest impact?",
        "How do you train new team members on these manual workflows?",
    ],
}

GENERIC_DISCOVERY_QUESTIONS = [
    "If you could wave a magic wand and fix one operational problem, what would it be?",
    "What is the cost of NOT fixing this problem over the next 12 months?",
    "Who else on your team feels this pain most acutely?",
]

# ═══════════════════════════════════════════════════════════
# SCORE INTERPRETATION
# ═══════════════════════════════════════════════════════════

def interpret_score(score: int) -> str:
    if score >= 80:
        return "Very High Opportunity — strong alignment with PNS solutions and significant savings potential."
    elif score >= 60:
        return "High Opportunity — clear automation potential with measurable ROI."
    elif score >= 40:
        return "Moderate Opportunity — worthwhile investigation with targeted automation."
    else:
        return "Developing Opportunity — may benefit from process review before automation."


# ═══════════════════════════════════════════════════════════
# INTLLIGENCE GENERATION
# ═══════════════════════════════════════════════════════════

def generate_intelligence(
    answers: dict,
    results: dict,
    company_data: dict,
    contact_data: dict,
) -> dict[str, Any]:
    """Generate structured assessment intelligence from raw inputs."""
    
    primary_problems: list[str] = answers.get("mainProblems", answers.get("main_problems", []))
    current_process: str = answers.get("currentProcess", answers.get("current_process", ""))
    weekly_time: str = answers.get("weeklyTimeSpent", answers.get("weekly_time_spent", ""))
    people: str = answers.get("peopleInvolved", answers.get("people_involved", ""))
    additional: str = answers.get("additionalDetails", answers.get("additional_details", ""))
    industry: str = company_data.get("industry", "")
    business_type: str = answers.get("businessType", "")

    # ── Primary pain point ──
    primary_pain = primary_problems[0] if primary_problems else "Unknown"
    
    # ── Recommended solutions ──
    solutions = _recommend_solutions(primary_problems, current_process, industry)
    
    # ── Discovery questions ──
    questions = _generate_discovery_questions(primary_problems, current_process)
    
    # ── Urgency ──
    time_info = TIME_BAND_URGENCY.get(weekly_time, {"urgency": "unknown", "message": "Time investment unknown."})
    
    # ── Project size ──
    project_size = PEOPLE_BAND_SIZE.get(people, "unknown")
    
    # ── Buying signals ──
    signals = _detect_buying_signals(primary_problems, current_process, weekly_time, additional)
    
    # ── Likely decision-maker ──
    decision_maker = _infer_decision_maker(people, primary_problems, current_process)
    
    # ── Next action ──
    priority = "high" if results.get("opportunityScore", 0) >= 70 else "medium" if results.get("opportunityScore", 0) >= 40 else "low"
    next_action = _recommend_next_action(priority, primary_pain, current_process, solutions)
    
    # ── Score interpretation ──
    score = results.get("opportunityScore", results.get("automation_score", 0))
    score_interpretation = interpret_score(score)
    
    # ── Root cause inference ──
    root_cause = _infer_root_cause(primary_problems, current_process, additional)
    
    # ── Business impact ──
    business_impact = _assess_business_impact(weekly_time, people, primary_problems, additional)

    return {
        # Pain & problems
        "primary_pain_point": primary_pain,
        "secondary_pain_points": primary_problems[1:] if len(primary_problems) > 1 else [],
        "current_process_summary": current_process,
        "root_cause": root_cause,
        "business_impact": business_impact,
        
        # Calculations
        "estimated_weekly_hours": results.get("estimatedWeeklyHours", 0),
        "estimated_annual_hours": results.get("estimatedAnnualHours", 0),
        "estimated_annual_labour_cost": results.get("estimatedAnnualLabourCost", 0),
        "estimated_annual_savings": results.get("estimatedAnnualSavings", results.get("estimated_annual_savings", 0)),
        "automation_score": score,
        "score_interpretation": score_interpretation,
        
        # Solutions
        "recommended_solution_categories": [s["category"] for s in solutions],
        "recommendation_reasons": [s["reason"] for s in solutions],
        "solutions_detail": solutions,
        
        # Sales intelligence
        "urgency": time_info["urgency"],
        "urgency_message": time_info["message"],
        "buying_signals": signals,
        "likely_decision_maker": decision_maker,
        "project_size_band": project_size,
        "priority": priority,
        
        # Actions
        "next_best_action": next_action,
        "discovery_questions": questions,
        
        # Metadata
        "intelligence_version": "1.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "confidence": 0.85,
        "source": "rule_engine",
    }


# ═══════════════════════════════════════════════════════════
# RECOMMENDATION ENGINE
# ═══════════════════════════════════════════════════════════

def _recommend_solutions(
    problems: list[str],
    process: str,
    industry: str,
) -> list[dict[str, Any]]:
    solutions: list[dict[str, Any]] = []
    seen_categories: set[str] = set()
    
    # 1. Problem-based recommendations
    for problem in problems:
        mapping = PROBLEM_SOLUTION_MAP.get(problem)
        if mapping and mapping["category"] not in seen_categories:
            solutions.append(mapping)
            seen_categories.add(mapping["category"])
    
    # 2. Process-based recommendation
    process_mapping = PROCESS_SOLUTION_MAP.get(process)
    if process_mapping and process_mapping["category"] not in seen_categories:
        solutions.append(process_mapping)
        seen_categories.add(process_mapping["category"])
    
    # 3. Industry-based recommendation
    industry_mapping = INDUSTRY_SOLUTION_MAP.get(industry)
    if industry_mapping and industry_mapping["category"] not in seen_categories:
        solutions.append(industry_mapping)
        seen_categories.add(industry_mapping["category"])
    
    # 4. Fallback
    if not solutions:
        solutions.append({
            "category": "Workflow Automation",
            "reason": "General process automation opportunity — requires discovery call to refine.",
            "confidence": 0.70,
        })
    
    return solutions


# ═══════════════════════════════════════════════════════════
# DISCOVERY QUESTIONS GENERATOR
# ═══════════════════════════════════════════════════════════

def _generate_discovery_questions(problems: list[str], process: str) -> list[str]:
    questions: list[str] = []
    seen: set[str] = set()
    
    # Problem-based questions
    for problem in problems:
        for q in DISCOVERY_QUESTIONS_BY_PROBLEM.get(problem, []):
            if q not in seen:
                questions.append(q)
                seen.add(q)
    
    # Process-based questions
    for q in DISCOVERY_QUESTIONS_BY_PROCESS.get(process, []):
        if q not in seen:
            questions.append(q)
            seen.add(q)
    
    # Top up with generic
    for q in GENERIC_DISCOVERY_QUESTIONS:
        if q not in seen and len(questions) < 5:
            questions.append(q)
            seen.add(q)
    
    return questions[:5]


# ═══════════════════════════════════════════════════════════
# BUYING SIGNAL DETECTION
# ═══════════════════════════════════════════════════════════

def _detect_buying_signals(
    problems: list[str],
    process: str,
    weekly_time: str,
    additional: str,
) -> list[str]:
    signals: list[str] = []
    
    # Time-based signals
    if weekly_time in ("More than 40 hours", "20–40 hours"):
        signals.append("High time cost — prospect is actively losing money on manual processes")
    
    # Process signals
    if process in ("Paper forms", "Manual processes"):
        signals.append("Legacy manual process — strong digital transformation opportunity")
    
    # Problem signals
    if any(p in problems for p in ["Repetitive data entry", "Reporting", "System integration"]):
        signals.append("Operational inefficiency — pain is measurable and recurring")
    
    # Additional detail signals
    if additional:
        lower = additional.lower()
        if any(w in lower for w in ["growing", "expanding", "scaling", "hiring"]):
            signals.append("Company is growing — automation needed to scale")
        if any(w in lower for w in ["frustrated", "tired of", "sick of", "waste"]):
            signals.append("Emotional pain language — high motivation to change")
        if any(w in lower for w in ["looking for", "evaluating", "researching", "shopping"]):
            signals.append("Active evaluation — prospect is comparing solutions")
    
    if not signals:
        signals.append("Initial inquiry — requires discovery to qualify further")
    
    return signals


# ═══════════════════════════════════════════════════════════
# DECISION MAKER INFERENCE
# ═══════════════════════════════════════════════════════════

def _infer_decision_maker(people: str, problems: list[str], process: str) -> str:
    if people in ("50+", "16-50"):
        if "Reporting" in problems or "Compliance and safety" in problems:
            return "Operations Director or VP Operations"
        return "CEO or COO (organization-wide impact)"
    elif people in ("6-15",):
        if process in ("Paper forms",):
            return "Operations Manager or Field Supervisor"
        return "General Manager or Owner"
    else:
        return "Owner or Department Manager"


# ═══════════════════════════════════════════════════════════
# NEXT ACTION RECOMMENDER
# ═══════════════════════════════════════════════════════════

def _recommend_next_action(
    priority: str,
    primary_pain: str,
    process: str,
    solutions: list[dict],
) -> str:
    solution_cat = solutions[0]["category"] if solutions else "Workflow Automation"
    
    if priority == "high":
        return (
            f"Call within 4 business hours. Qualify the {process.lower() if process else 'manual'} "
            f"workflow. Propose a {solution_cat.lower()} discovery session."
        )
    elif priority == "medium":
        return (
            f"Email within 24 hours with a {solution_cat} case study. "
            f"Schedule a 15-minute qualification call this week."
        )
    else:
        return (
            "Add to nurture sequence. Send relevant content about automation "
            "for companies of similar size. Re-evaluate in 30 days."
        )


# ═══════════════════════════════════════════════════════════
# ROOT CAUSE INFERENCE
# ═══════════════════════════════════════════════════════════

def _infer_root_cause(problems: list[str], process: str, additional: str) -> str:
    if process == "Paper forms" and "Repetitive data entry" in problems:
        return "Information trapped on paper requires manual re-entry into digital systems — creating a costly paper-to-digital bridge with no automation."
    elif process == "Spreadsheets" and "Reporting" in problems:
        return "Spreadsheets are being used as databases — manual compilation for reporting creates errors and delays."
    elif "Multiple software tools" in process and "System integration" in problems:
        return "Disconnected tools create data silos — no single source of truth forces manual reconciliation."
    elif "Managing documents" in problems:
        return "Documents lack centralized storage and retrieval — manual classification and search create friction."
    elif additional and len(additional) > 10:
        return f"Based on additional context: {additional[:200]}"
    return "Manual processes without automation create compounding inefficiency across the workflow."


# ═══════════════════════════════════════════════════════════
# BUSINESS IMPACT ASSESSMENT
# ═══════════════════════════════════════════════════════════

def _assess_business_impact(
    weekly_time: str,
    people: str,
    problems: list[str],
    additional: str,
) -> str:
    time_desc = weekly_time.replace("\u2013", "-") if weekly_time else "unknown"
    people_desc = people if people else "unknown number of"
    
    base = f"Estimated {time_desc} per week across {people_desc} people. "
    
    if "Repetitive data entry" in problems:
        base += "Manual data entry creates a recurring tax on team productivity and introduces errors. "
    if "Reporting" in problems:
        base += "Manual reporting delays decision-making and consumes skilled time on compilation instead of analysis. "
    if "Managing documents" in problems:
        base += "Document mismanagement creates compliance risk and slows information retrieval. "
    if "Customer communication" in problems:
        base += "Inconsistent customer communication risks lost revenue and damaged relationships. "
    
    return base.strip()
