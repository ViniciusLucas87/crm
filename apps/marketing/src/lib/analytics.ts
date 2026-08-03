/**
 * Privacy-respecting first-party funnel event tracking.
 *
 * No-ops until a provider is configured. Never loads third-party cookies,
 * scripts, or pixels. Designed for future configuration via environment
 * variable (NEXT_PUBLIC_ANALYTICS_PROVIDER) without code changes.
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

let _queue: Array<{ event: FunnelEvent; payload: EventPayload; ts: number }> = [];
const MAX_QUEUE = 100;

function _flush() {
  if (!ANALYTICS_PROVIDER || _queue.length === 0) return;
  const batch = _queue.splice(0);
  try {
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
  if (!ANALYTICS_PROVIDER) return;

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
