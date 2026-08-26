/**
 * Privacy-respecting first-party funnel event tracking.
 *
 * Uses GA4 when a public measurement ID is configured and continues to
 * support the existing Plausible option. Event payloads must not contain
 * names, email addresses, phone numbers, or other personal information.
 */

type FunnelEvent =
  | "tool_view"
  | "tool_started"
  | "tool_step_completed"
  | "tool_completed"
  | "contact_started"
  | "lead_submitted";

interface EventPayload {
  tool?: string;
  step?: number;
  [key: string]: unknown;
}

const ANALYTICS_PROVIDER =
  typeof process !== "undefined" &&
  process.env?.NEXT_PUBLIC_ANALYTICS_PROVIDER;
const GOOGLE_ANALYTICS_ID =
  typeof process !== "undefined" &&
  process.env?.NEXT_PUBLIC_GA_MEASUREMENT_ID;

let _queue: Array<{ event: FunnelEvent; payload: EventPayload; ts: number }> = [];
const MAX_QUEUE = 100;

function _flush() {
  if (_queue.length === 0) return;
  const batch = _queue.splice(0);
  try {
    if (GOOGLE_ANALYTICS_ID && typeof window !== "undefined") {
      const gtag = (window as unknown as {
        gtag?: (command: "event", event: string, payload: EventPayload) => void;
      }).gtag;
      for (const { event, payload } of batch) {
        gtag?.("event", event, payload);
      }
    }
    if (ANALYTICS_PROVIDER === "plausible" && typeof window !== "undefined") {
      const plausible = (
        window as unknown as {
          plausible?: (event: string, options: { props: EventPayload }) => void;
        }
      ).plausible;
      for (const { event, payload } of batch) {
        plausible?.(event, { props: payload });
      }
    }
    /* Add additional providers here when configured */
  } catch {
    /* analytics failure must never break the application */
  }
}

export function track(event: FunnelEvent, payload: EventPayload = {}): void {
  if (!ANALYTICS_PROVIDER && !GOOGLE_ANALYTICS_ID) return;

  _queue.push({ event, payload, ts: Date.now() });
  if (_queue.length > MAX_QUEUE) _queue.shift();

  if (typeof window !== "undefined") {
    /* Flush on next idle callback to avoid blocking the main thread */
    if ("requestIdleCallback" in window) {
      window.requestIdleCallback(() => _flush());
    } else {
      setTimeout(_flush, 0);
    }
  }
}

/** Exposed for testing only — clears the internal queue. */
export function _testReset(): void {
  _queue = [];
}
