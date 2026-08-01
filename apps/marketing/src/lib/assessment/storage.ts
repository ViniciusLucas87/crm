import type { AssessmentState } from "./types";
import { ASSESSMENT_STORAGE_KEY, ASSESSMENT_VERSION } from "./types";

export function saveToSession(state: AssessmentState): void {
  try {
    const payload = { ...state };
    // Strip contact info from session storage for privacy
    delete payload.contactName;
    delete payload.contactEmail;
    delete payload.contactCompany;
    delete payload.contactPhone;
    delete payload.additionalDetails;

    sessionStorage.setItem(ASSESSMENT_STORAGE_KEY, JSON.stringify(payload));
  } catch {
    // Storage unavailable , silently fail
  }
}

export function loadFromSession(): AssessmentState | null {
  try {
    const raw = sessionStorage.getItem(ASSESSMENT_STORAGE_KEY);
    if (!raw) return null;

    const parsed = JSON.parse(raw);

    if (parsed.version !== ASSESSMENT_VERSION) {
      sessionStorage.removeItem(ASSESSMENT_STORAGE_KEY);
      return null;
    }

    return parsed as AssessmentState;
  } catch {
    return null;
  }
}

export function clearSession(): void {
  try {
    sessionStorage.removeItem(ASSESSMENT_STORAGE_KEY);
  } catch {
    // Silently fail
  }
}

