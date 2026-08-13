import type { AssessmentState, AssessmentResults, OpportunityCard } from "./types";
import {
  TIME_RANGE_HOURS,
  PEOPLE_RANGE_COUNT,
  DEFAULT_LOADED_WAGE,
  DEFAULT_WORKING_WEEKS,
  AUTOMATION_RECOVERY_RATE,
} from "./types";

/** Problem → recommendation mapping */
const PROBLEM_OPPORTUNITIES: Record<string, { label: string; description: string }> = {
  "Repetitive data entry": {
    label: "Automate data entry",
    description: "Connect your systems so information flows automatically , enter it once, use it everywhere.",
  },
  "Scheduling and dispatching": {
    label: "Smart scheduling",
    description: "Replace manual coordination with a system that optimizes assignments based on availability, location, and priority.",
  },
  "Managing documents": {
    label: "Document automation",
    description: "Auto-generate, organize, and search documents , eliminate the filing-cabinet workflow.",
  },
  "Reporting": {
    label: "Automated reporting",
    description: "Turn raw data into live dashboards and scheduled reports without manual spreadsheet assembly.",
  },
  "Customer follow up": {
    label: "Streamline follow up",
    description: "Automate reminders, status updates, and follow up sequences so nothing falls through the cracks.",
  },
  "Information spread across different systems": {
    label: "System integration",
    description: "Unify your tools so your team works from a single source of truth instead of hopping between platforms.",
  },
  "Manual approvals": {
    label: "Workflow automation",
    description: "Replace email-chain approvals with structured digital workflows that route decisions to the right people automatically.",
  },
  "Other": {
    label: "Custom process improvement",
    description: "Every business has unique friction points , we'll identify and solve yours with tailored software.",
  },
};

export function calculateAllResults(state: AssessmentState): AssessmentResults {
  const weeklyHours = TIME_RANGE_HOURS[state.weeklyTimeSpent ?? "Not sure"] ?? 10;
  const peopleCount = PEOPLE_RANGE_COUNT[state.peopleInvolved ?? "2–5"] ?? 3.5;
  const annualHours = weeklyHours * peopleCount * DEFAULT_WORKING_WEEKS;
  const annualLabourCost = annualHours * DEFAULT_LOADED_WAGE;
  const annualSavings = annualLabourCost * AUTOMATION_RECOVERY_RATE;

  const opportunityScore = calculateOpportunityScore(state, weeklyHours, peopleCount);
  const scoreInterpretation = interpretScore(opportunityScore);
  const topOpportunities = getTopOpportunities(state.mainProblems);
  const aiReadiness = calculateAIReadiness(state);
  const assumptions = generateAssumptions(weeklyHours, peopleCount);

  return {
    opportunityScore,
    scoreInterpretation,
    estimatedWeeklyHours: Math.round(weeklyHours * peopleCount),
    estimatedAnnualHours: Math.round(annualHours),
    estimatedPeopleCount: peopleCount,
    estimatedAnnualLabourCost: Math.round(annualLabourCost),
    estimatedAnnualSavings: Math.round(annualSavings),
    topOpportunities,
    aiReadiness,
    assumptions,
  };
}

function calculateOpportunityScore(
  state: AssessmentState,
  weeklyHours: number,
  peopleCount: number,
): number {
  const problemCount = state.mainProblems.length;

  // Problem severity: more problems = higher score (max 30)
  const problemScore = Math.min(problemCount * 6, 30);

  // Time factor: more hours = higher score (max 35)
  const timeScore = Math.min((weeklyHours / 50) * 35, 35);

  // People factor: more people = higher score (max 20)
  const peopleScore = Math.min((peopleCount / 75) * 20, 20);

  // Process factor: manual/paper/email/spreadsheet-based = higher score (max 15)
  const process = state.currentProcess ?? "";
  let processScore = 5; // default mid
  if (["Paper forms", "Mostly manual", "Email", "Spreadsheets"].includes(process)) {
    processScore = 15;
  } else if (["Multiple software tools"].includes(process)) {
    processScore = 10;
  } else if (["Existing custom system"].includes(process)) {
    processScore = 3;
  }

  return Math.round(Math.min(problemScore + timeScore + peopleScore + processScore, 100));
}

function interpretScore(score: number): string {
  if (score >= 75) return "Very High , major automation opportunity";
  if (score >= 50) return "High , significant automation opportunity";
  if (score >= 30) return "Moderate , notable automation opportunity";
  return "Lower , may still benefit from targeted automation";
}

function getTopOpportunities(problems: string[]): OpportunityCard[] {
  if (problems.length === 0) {
    return [
      { label: "Workflow assessment", description: "Book an audit so we can identify your top automation opportunities together.", rank: 1 },
    ];
  }

  return problems
    .map((p) => {
      const match = PROBLEM_OPPORTUNITIES[p] ?? PROBLEM_OPPORTUNITIES["Other"];
      return { label: match.label, description: match.description, rank: 0 };
    })
    .slice(0, 3)
    .map((o, i) => ({ ...o, rank: i + 1 }));
}

function calculateAIReadiness(state: AssessmentState) {
  const process = state.currentProcess ?? "";

  if (["Paper forms", "Mostly manual"].includes(process)) {
    return { level: "foundation-needed", label: "Foundation needed , digitize core processes first" };
  }
  if (["Spreadsheets", "Email"].includes(process)) {
    return { level: "partially-ready", label: "Partially ready , good data exists but needs structure" };
  }
  if (["Multiple software tools"].includes(process)) {
    return { level: "partially-ready", label: "Partially ready , systems exist but need integration" };
  }
  if (["Existing custom system"].includes(process)) {
    return { level: "ready-focused", label: "Ready for focused AI and automation" };
  }
  return { level: "partially-ready", label: "Partially ready , we'll assess readiness in the audit" };
}

function generateAssumptions(weeklyHours: number, peopleCount: number): string[] {
  return [
    `Based on ~${Math.round(weeklyHours)} hrs/week across ${peopleCount > 1 ? `~${peopleCount} people` : "1 person"}.`,
    `Assumes CAD $${DEFAULT_LOADED_WAGE}/hr loaded labour cost and ${DEFAULT_WORKING_WEEKS} working weeks/year.`,
    `Automation recovery estimated at ${Math.round(AUTOMATION_RECOVERY_RATE * 100)}% of repetitive time.`,
    "This is a directional estimate , actual results depend on your specific workflows and implementation.",
    "Book a free Operations Audit for a detailed, personalized assessment.",
  ];
}

