/** Simplified 6-step assessment , ~2 minutes to complete */

export interface AssessmentState {
  version: number;

  // Step 1: Business type
  businessType?: string;

  // Step 2: Main operational problems (multi-select)
  mainProblems: string[];

  // Step 3: Current process
  currentProcess?: string;

  // Step 4: Weekly time spent range
  weeklyTimeSpent?: string;

  // Step 5: People involved range
  peopleInvolved?: string;

  // Step 6: Contact
  preferredContactMethod?: string;
  contactName?: string;
  contactEmail?: string;
  contactCompany?: string;
  contactPhone?: string;
  bestTimeToContact?: string;
  additionalDetails?: string;

  currentStep: number;
}

export interface AssessmentResults {
  // Score
  opportunityScore: number;
  scoreInterpretation: string;

  // Time & cost estimates
  estimatedWeeklyHours: number;
  estimatedAnnualHours: number;
  estimatedPeopleCount: number;
  estimatedAnnualLabourCost: number;
  estimatedAnnualSavings: number;

  // Top opportunities
  topOpportunities: OpportunityCard[];

  // AI readiness (simplified)
  aiReadiness: { level: string; label: string };

  // Assumptions
  assumptions: string[];
}

export interface OpportunityCard {
  label: string;
  description: string;
  rank: number;
}

export const ASSESSMENT_STORAGE_KEY = "pns_automation_assessment_v2";
export const ASSESSMENT_VERSION = 2;

/** Midpoint hours for each range option */
export const TIME_RANGE_HOURS: Record<string, number> = {
  "Less than 5 hours": 3,
  "5–10 hours": 7.5,
  "10–20 hours": 15,
  "20–40 hours": 30,
  "More than 40 hours": 50,
  "Not sure": 10,
};

/** Midpoint people for each range option */
export const PEOPLE_RANGE_COUNT: Record<string, number> = {
  "1": 1,
  "2–5": 3.5,
  "6–15": 10.5,
  "16–50": 33,
  "50+": 75,
};

export const DEFAULT_LOADED_WAGE = 45; // CAD/hr assumed loaded cost
export const DEFAULT_WORKING_WEEKS = 50;
export const AUTOMATION_RECOVERY_RATE = 0.35; // 35% of repetitive time is recoverable

