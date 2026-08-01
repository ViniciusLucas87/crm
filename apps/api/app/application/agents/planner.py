"""
AI Task Planner.

Breaks user goals into structured agent task plans.
The planner decides which agents to invoke, in what order,
and what context each agent needs.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PlanStep:
    """A single step in an execution plan."""
    agent_name: str
    description: str
    input_context: dict[str, Any] = field(default_factory=dict)
    depends_on: list[int] = field(default_factory=list)  # indices of previous steps
    can_parallel: bool = False
    needs_approval: bool = False


@dataclass
class ExecutionPlan:
    """A complete multi-agent execution plan."""
    goal: str
    steps: list[PlanStep]
    estimated_steps: int
    reasoning: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "steps": [
                {"agent": s.agent_name, "description": s.description, "depends_on": s.depends_on, "needs_approval": s.needs_approval}
                for s in self.steps
            ],
            "estimated_steps": self.estimated_steps,
            "reasoning": self.reasoning,
        }


class Planner:
    """
    Rule-based task planner.

    Given a user goal, determines which agents to invoke and in what order.
    Uses keyword matching and context analysis — no LLM required for planning.
    """

    # Keyword → agent workflow mapping
    WORKFLOWS: dict[str, list[tuple[str, str]]] = {
        "research": [
            ("sales_research", "Research company intelligence and detect buying signals"),
            ("sales_research", "Calculate opportunity score and recommend services"),
        ],
        "proposal": [
            ("sales_research", "Gather company intelligence and signals"),
            ("proposal_writer", "Generate proposal draft with pricing"),
            ("sales_research", "Create follow-up task"),
        ],
        "meeting": [
            ("meeting_prep", "Prepare meeting briefing with questions and objections"),
            ("sales_research", "Refresh company research before meeting"),
        ],
        "pipeline": [
            ("pipeline_coach", "Analyze pipeline health and detect risks"),
            ("sales_research", "Refresh scores for at-risk deals"),
        ],
        "daily": [
            ("daily_operations", "Generate daily brief with priorities"),
        ],
        "outreach": [
            ("outreach", "Generate outreach messages"),
        ],
        "account": [
            ("account_growth", "Analyze growth opportunities"),
        ],
        "summarize": [
            ("sales_research", "Generate company summary and analysis"),
        ],
    }

    @classmethod
    def plan(cls, goal: str, context: dict[str, Any] | None = None) -> ExecutionPlan:
        """Create an execution plan from a user goal."""
        goal_lower = goal.lower().strip()
        ctx = context or {}

        # Match goal to workflow
        matched_workflow: list[tuple[str, str]] = []
        matched_keyword = "general"

        for keyword, workflow in cls.WORKFLOWS.items():
            if keyword in goal_lower:
                matched_workflow = workflow
                matched_keyword = keyword
                break

        # If no match, try partial matches
        if not matched_workflow:
            if any(w in goal_lower for w in ["score", "signal", "opportunity", "buying"]):
                matched_workflow = cls.WORKFLOWS["research"]
                matched_keyword = "research"
            elif any(w in goal_lower for w in ["brief", "today", "morning", "priority"]):
                matched_workflow = cls.WORKFLOWS["daily"]
                matched_keyword = "daily"
            else:
                matched_workflow = cls.WORKFLOWS["research"]
                matched_keyword = "research"

        # Build steps
        steps: list[PlanStep] = []
        for agent_name, description in matched_workflow:
            step = PlanStep(
                agent_name=agent_name,
                description=description,
                input_context={"goal": goal, **ctx},
                needs_approval=agent_name in ("pipeline_coach", "account_growth"),
            )
            steps.append(step)

        reasoning = f"Matched keyword '{matched_keyword}'. Executing {len(steps)} agent step(s)."

        return ExecutionPlan(
            goal=goal,
            steps=steps,
            estimated_steps=len(steps),
            reasoning=reasoning,
        )
