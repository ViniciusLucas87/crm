/**
 * Browser submission recovery storage.
 *
 * Policy A: Pending submissions are stored in localStorage as a
 * recovery mechanism when the CRM intake endpoint is unreachable.
 *
 * Limitations (documented):
 * - Survives: browser restart, tab close, session expiry
 * - Does NOT survive: browser data deletion, different device
 *
 * Future Policy B: replace with server-side outbox queue.
 */

const STORAGE_KEY_PREFIX = "pns_submission_";
const SCHEMA_VERSION = 1;
const MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000; // 7 days

interface StoredSubmission {
  version: number;
  requestId: string;
  savedAt: string; // ISO-8601
  expiresAt: string; // ISO-8601
  payload: unknown;
}

export interface StorageResult {
  ok: boolean;
  error?: "quota_exceeded" | "disabled" | "unknown";
}

/** Check if localStorage is available and writable. */
export function isStorageAvailable(): boolean {
  try {
    const testKey = `${STORAGE_KEY_PREFIX}__test__`;
    localStorage.setItem(testKey, "1");
    localStorage.removeItem(testKey);
    return true;
  } catch {
    return false;
  }
}

/** Save a submission for recovery. Returns result with success/failure reason. */
export function saveSubmission(requestId: string, payload: unknown): StorageResult {
  try {
    const entry: StoredSubmission = {
      version: SCHEMA_VERSION,
      requestId,
      savedAt: new Date().toISOString(),
      expiresAt: new Date(Date.now() + MAX_AGE_MS).toISOString(),
      payload,
    };
    localStorage.setItem(
      `${STORAGE_KEY_PREFIX}${requestId}`,
      JSON.stringify(entry),
    );
    return { ok: true };
  } catch (err) {
    const msg = String(err);
    if (msg.includes("quota") || msg.includes("QuotaExceeded")) {
      return { ok: false, error: "quota_exceeded" };
    }
    return { ok: false, error: "disabled" };
  }
}

/** Load a saved submission. Returns null if missing, expired, malformed, or wrong version. */
export function loadSubmission(requestId: string): unknown | null {
  try {
    const raw = localStorage.getItem(`${STORAGE_KEY_PREFIX}${requestId}`);
    if (!raw) return null;

    const entry: StoredSubmission = JSON.parse(raw);

    // Schema version check
    if (!entry || entry.version !== SCHEMA_VERSION) {
      removeSubmission(requestId);
      return null;
    }

    // Expiry check
    if (entry.expiresAt && new Date(entry.expiresAt) < new Date()) {
      removeSubmission(requestId);
      return null;
    }

    return entry.payload;
  } catch {
    // Malformed JSON — clean up
    removeSubmission(requestId);
    return null;
  }
}

/** Remove a submission from storage. */
export function removeSubmission(requestId: string): void {
  try {
    localStorage.removeItem(`${STORAGE_KEY_PREFIX}${requestId}`);
  } catch {
    // Storage unavailable — nothing to do
  }
}

/**
 * Clean up all expired or malformed submissions on page load.
 * Call once on mount.
 */
export function cleanExpiredSubmissions(): void {
  try {
    const keysToRemove: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (!key || !key.startsWith(STORAGE_KEY_PREFIX)) continue;

      try {
        const raw = localStorage.getItem(key);
        if (!raw) { keysToRemove.push(key); continue; }

        const entry: StoredSubmission = JSON.parse(raw);
        if (!entry || entry.version !== SCHEMA_VERSION) {
          keysToRemove.push(key);
          continue;
        }
        if (entry.expiresAt && new Date(entry.expiresAt) < new Date()) {
          keysToRemove.push(key);
        }
      } catch {
        keysToRemove.push(key);
      }
    }
    for (const key of keysToRemove) {
      localStorage.removeItem(key);
    }
  } catch {
    // Storage unavailable — nothing to clean
  }
}
