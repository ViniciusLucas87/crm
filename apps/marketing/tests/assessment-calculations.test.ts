import { describe, it, expect } from "vitest";
import { calculateAllResults } from "@/lib/assessment/calculations";
import type { AssessmentState } from "@/lib/assessment/types";

function makeState(overrides: Partial<AssessmentState> = {}): AssessmentState {
  return {
    version: 1,
    mainProblems: ["Repetitive data entry", "Manual approvals"],
    currentStep: 1,
    businessType: "Construction",
    currentProcess: "Spreadsheets and email",
    weeklyTimeSpent: "10–20 hours",
    peopleInvolved: "2–5",
    ...overrides,
  };
}

describe("calculateAllResults", () => {
  it("returns all expected result keys", () => {
    const result = calculateAllResults(makeState());
    expect(result).toHaveProperty("opportunityScore");
    expect(result).toHaveProperty("estimatedAnnualHours");
    expect(result).toHaveProperty("estimatedAnnualSavings");
    expect(result).toHaveProperty("topOpportunities");
    expect(result).toHaveProperty("assumptions");
  });

  it("calculates positive savings", () => {
    const result = calculateAllResults(makeState());
    expect(result.estimatedAnnualSavings).toBeGreaterThan(0);
    expect(result.estimatedAnnualLabourCost).toBeGreaterThan(0);
  });

  it("more problems = higher score", () => {
    const few = calculateAllResults(makeState({ mainProblems: ["Reporting"] }));
    const many = calculateAllResults(makeState({ mainProblems: ["Repetitive data entry", "Manual approvals", "Scheduling and dispatching", "Managing documents", "Reporting"] }));
    expect(many.opportunityScore).toBeGreaterThan(few.opportunityScore);
  });

  it("more time = higher savings", () => {
    const low = calculateAllResults(makeState({ weeklyTimeSpent: "Less than 5 hours" }));
    const high = calculateAllResults(makeState({ weeklyTimeSpent: "40+ hours" }));
    expect(high.estimatedAnnualSavings).toBeGreaterThan(low.estimatedAnnualSavings);
  });

  it("more people = higher savings", () => {
    const few = calculateAllResults(makeState({ peopleInvolved: "2–5" }));
    const many = calculateAllResults(makeState({ peopleInvolved: "6–15" }));
    expect(many.estimatedAnnualSavings).toBeGreaterThan(few.estimatedAnnualSavings);
  });

  it("generates opportunities matching problem categories", () => {
    const result = calculateAllResults(makeState({ mainProblems: ["Repetitive data entry"] }));
    expect(result.topOpportunities.length).toBeGreaterThan(0);
    expect(result.topOpportunities[0]).toHaveProperty("label");
    expect(result.topOpportunities[0]).toHaveProperty("description");
  });

  it("handles empty state gracefully", () => {
    const result = calculateAllResults({ version: 1, mainProblems: [], currentStep: 1 });
    expect(result.opportunityScore).toBeGreaterThanOrEqual(0);
    expect(result.estimatedAnnualSavings).toBeGreaterThanOrEqual(0);
  });
});
