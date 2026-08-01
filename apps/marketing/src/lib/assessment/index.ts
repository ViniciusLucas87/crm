export {
  businessTypeSchema,
  mainProblemsSchema,
  currentProcessSchema,
  weeklyTimeSchema,
  peopleInvolvedSchema,
  contactSchema,
} from "./schema";

export { calculateAllResults } from "./calculations";

export { saveToSession, loadFromSession, clearSession } from "./storage";

export type { AssessmentState, AssessmentResults, OpportunityCard } from "./types";

export {
  ASSESSMENT_VERSION,
  TIME_RANGE_HOURS,
  PEOPLE_RANGE_COUNT,
  DEFAULT_LOADED_WAGE,
  DEFAULT_WORKING_WEEKS,
} from "./types";

