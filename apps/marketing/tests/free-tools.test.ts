import { describe, it, expect } from "vitest";

/* ------------------------------------------------------------------ */
/*  Manual Work Cost Calculator                                        */
/* ------------------------------------------------------------------ */

// Inline calculation logic for unit testing
interface ManualWorkInput {
  employeesAffected: number;
  hoursPerWeek: number;
  loadedHourlyCost: number;
  weeksPerYear: number;
  recoverablePercent: number;
}

function calculate(input: ManualWorkInput) {
  const weeklyHours = input.employeesAffected * input.hoursPerWeek;
  const annualHours = weeklyHours * input.weeksPerYear;
  const weeklyCost = weeklyHours * input.loadedHourlyCost;
  const annualCost = annualHours * input.loadedHourlyCost;
  const recoverableHours = annualHours * (input.recoverablePercent / 100);
  const recoverableCost = recoverableHours * input.loadedHourlyCost;

  return {
    weeklyHours: Math.round(weeklyHours * 10) / 10,
    annualHours: Math.round(annualHours),
    weeklyCost: Math.round(weeklyCost),
    annualCost: Math.round(annualCost),
    recoverableHours: Math.round(recoverableHours),
    recoverableCost: Math.round(recoverableCost),
  };
}

describe("Manual Work Cost Calculator", () => {
  it("calculates correctly for a typical 5-person team", () => {
    const result = calculate({
      employeesAffected: 5,
      hoursPerWeek: 10,
      loadedHourlyCost: 35,
      weeksPerYear: 48,
      recoverablePercent: 35,
    });
    expect(result.weeklyHours).toBe(50);
    expect(result.annualHours).toBe(2400);
    expect(result.weeklyCost).toBe(1750);
    expect(result.annualCost).toBe(84000);
    expect(result.recoverableHours).toBe(840);
    expect(result.recoverableCost).toBe(29400);
  });

  it("handles single employee edge case", () => {
    const result = calculate({
      employeesAffected: 1,
      hoursPerWeek: 2,
      loadedHourlyCost: 25,
      weeksPerYear: 46,
      recoverablePercent: 10,
    });
    expect(result.weeklyHours).toBe(2);
    expect(result.annualHours).toBe(92);
    expect(result.recoverableHours).toBe(9);
  });

  it("handles maximum recovery rate", () => {
    const result = calculate({
      employeesAffected: 10,
      hoursPerWeek: 40,
      loadedHourlyCost: 75,
      weeksPerYear: 52,
      recoverablePercent: 80,
    });
    expect(result.annualCost).toBe(1560000);
    expect(result.recoverableCost).toBe(1248000);
  });

  it("zero recovery yields zero recoverable cost", () => {
    const result = calculate({
      employeesAffected: 3,
      hoursPerWeek: 5,
      loadedHourlyCost: 30,
      weeksPerYear: 48,
      recoverablePercent: 0,
    });
    expect(result.recoverableHours).toBe(0);
    expect(result.recoverableCost).toBe(0);
  });

  it("produces integer annual costs", () => {
    const result = calculate({
      employeesAffected: 2,
      hoursPerWeek: 7,
      loadedHourlyCost: 33,
      weeksPerYear: 50,
      recoverablePercent: 40,
    });
    expect(Number.isInteger(result.annualCost)).toBe(true);
    expect(Number.isInteger(result.recoverableCost)).toBe(true);
  });
});

/* ------------------------------------------------------------------ */
/*  CRM Readiness Score Bands                                          */
/* ------------------------------------------------------------------ */

function getBand(percentage: number): string {
  if (percentage >= 80) return "Optimized";
  if (percentage >= 60) return "Developing";
  if (percentage >= 35) return "Foundational";
  return "Starting Out";
}

describe("CRM Readiness Score Bands", () => {
  it("scores 100 as Optimized", () => {
    expect(getBand(100)).toBe("Optimized");
  });
  it("scores 80 as Optimized (boundary)", () => {
    expect(getBand(80)).toBe("Optimized");
  });
  it("scores 79 as Developing", () => {
    expect(getBand(79)).toBe("Developing");
  });
  it("scores 60 as Developing (boundary)", () => {
    expect(getBand(60)).toBe("Developing");
  });
  it("scores 59 as Foundational", () => {
    expect(getBand(59)).toBe("Foundational");
  });
  it("scores 35 as Foundational (boundary)", () => {
    expect(getBand(35)).toBe("Foundational");
  });
  it("scores 34 as Starting Out", () => {
    expect(getBand(34)).toBe("Starting Out");
  });
  it("scores 0 as Starting Out", () => {
    expect(getBand(0)).toBe("Starting Out");
  });
  it("handles negative score gracefully", () => {
    expect(getBand(-1)).toBe("Starting Out");
  });
});

/* ------------------------------------------------------------------ */
/*  Automation ROI Calculator                                          */
/* ------------------------------------------------------------------ */

interface ROIInput {
  implementationCost: number;
  monthlyRecurringCost: number;
  peopleAffected: number;
  hoursSavedPerWeek: number;
  loadedHourlyCost: number;
  additionalMonthlyRevenue: number;
}

function calculateROI(input: ROIInput) {
  const monthlyLabourSaving =
    input.peopleAffected * input.hoursSavedPerWeek * 4.33 * input.loadedHourlyCost;
  const grossMonthlyBenefit = monthlyLabourSaving + input.additionalMonthlyRevenue;
  const grossAnnualBenefit = grossMonthlyBenefit * 12;
  const totalYearOneCost = input.implementationCost + input.monthlyRecurringCost * 12;
  const netYearOneBenefit = grossAnnualBenefit - totalYearOneCost;
  const netMonthlyBenefit = grossMonthlyBenefit - input.monthlyRecurringCost;
  const paybackMonths =
    netMonthlyBenefit > 0
      ? Math.ceil((input.implementationCost / netMonthlyBenefit) * 10) / 10
      : Infinity;
  const yearOneROI =
    totalYearOneCost > 0
      ? Math.round(((netYearOneBenefit / totalYearOneCost) * 100) * 10) / 10
      : 0;
  return {
    grossMonthlyBenefit: Math.round(grossMonthlyBenefit),
    grossAnnualBenefit: Math.round(grossAnnualBenefit),
    netYearOneBenefit: Math.round(netYearOneBenefit),
    paybackMonths,
    yearOneROI,
  };
}

describe("Automation ROI Calculator", () => {
  it("calculates positive ROI for a standard case", () => {
    const result = calculateROI({
      implementationCost: 15000,
      monthlyRecurringCost: 500,
      peopleAffected: 3,
      hoursSavedPerWeek: 10,
      loadedHourlyCost: 35,
      additionalMonthlyRevenue: 0,
    });
    // 3 * 10 * 4.33 * 35 = 4546.5/month labour
    expect(result.grossMonthlyBenefit).toBe(4547);
    expect(result.netYearOneBenefit).toBeGreaterThan(0);
    expect(result.paybackMonths).toBeLessThan(12);
    expect(result.yearOneROI).toBeGreaterThan(0);
  });

  it("shows negative ROI when costs exceed benefits", () => {
    const result = calculateROI({
      implementationCost: 50000,
      monthlyRecurringCost: 2000,
      peopleAffected: 1,
      hoursSavedPerWeek: 2,
      loadedHourlyCost: 25,
      additionalMonthlyRevenue: 0,
    });
    expect(result.netYearOneBenefit).toBeLessThan(0);
    expect(result.yearOneROI).toBeLessThan(0);
  });

  it("includes additional monthly revenue in benefit", () => {
    const noRevenue = calculateROI({
      implementationCost: 10000,
      monthlyRecurringCost: 200,
      peopleAffected: 2,
      hoursSavedPerWeek: 5,
      loadedHourlyCost: 30,
      additionalMonthlyRevenue: 0,
    });
    const withRevenue = calculateROI({
      implementationCost: 10000,
      monthlyRecurringCost: 200,
      peopleAffected: 2,
      hoursSavedPerWeek: 5,
      loadedHourlyCost: 30,
      additionalMonthlyRevenue: 2000,
    });
    expect(withRevenue.grossMonthlyBenefit).toBeGreaterThan(noRevenue.grossMonthlyBenefit);
  });

  it("handles zero-cost edge case", () => {
    const result = calculateROI({
      implementationCost: 0,
      monthlyRecurringCost: 0,
      peopleAffected: 1,
      hoursSavedPerWeek: 1,
      loadedHourlyCost: 20,
      additionalMonthlyRevenue: 0,
    });
    expect(result.paybackMonths).toBe(0);
  });

  it("handles infinite payback when no monthly benefit", () => {
    const result = calculateROI({
      implementationCost: 10000,
      monthlyRecurringCost: 0,
      peopleAffected: 0,
      hoursSavedPerWeek: 0,
      loadedHourlyCost: 0,
      additionalMonthlyRevenue: 0,
    });
    expect(result.paybackMonths).toBe(Infinity);
    expect(result.netYearOneBenefit).toBeLessThan(0);
  });

  it("has no payback when recurring costs exceed monthly benefit", () => {
    const result = calculateROI({
      implementationCost: 10000,
      monthlyRecurringCost: 1000,
      peopleAffected: 1,
      hoursSavedPerWeek: 1,
      loadedHourlyCost: 20,
      additionalMonthlyRevenue: 0,
    });
    expect(result.paybackMonths).toBe(Infinity);
  });

  it("returns integer financial values", () => {
    const result = calculateROI({
      implementationCost: 12000,
      monthlyRecurringCost: 350,
      peopleAffected: 4,
      hoursSavedPerWeek: 8,
      loadedHourlyCost: 40,
      additionalMonthlyRevenue: 500,
    });
    expect(Number.isInteger(result.grossMonthlyBenefit)).toBe(true);
    expect(Number.isInteger(result.grossAnnualBenefit)).toBe(true);
    expect(Number.isInteger(result.netYearOneBenefit)).toBe(true);
  });
});

/* ------------------------------------------------------------------ */
/*  Analytics abstraction                                               */
/* ------------------------------------------------------------------ */

describe("Analytics abstraction", () => {
  it("no-ops when no provider configured", async () => {
    const { track } = await import("@/lib/analytics");
    expect(() => track("tool_view", { tool: "test" })).not.toThrow();
  });
});
