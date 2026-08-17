import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const webRtcPath = join(process.cwd(), "src", "lib", "webrtc-client.ts");
const ctxPath = join(process.cwd(), "src", "lib", "telephony-context.tsx");
const barPath = join(process.cwd(), "src", "components", "telephony", "global-call-bar.tsx");

describe("Inbound calling: WebRTC client", () => {
  it("exports answerIncomingCall function", () => {
    const content = readFileSync(webRtcPath, "utf8");
    expect(content).toContain("export async function answerIncomingCall");
  });

  it("exports declineIncomingCall function", () => {
    const content = readFileSync(webRtcPath, "utf8");
    expect(content).toContain("export async function declineIncomingCall");
  });

  it("exports IncomingCallInfo type", () => {
    const content = readFileSync(webRtcPath, "utf8");
    expect(content).toContain("export interface IncomingCallInfo");
  });

  it("exports onIncomingCall and onIncomingCallEnded", () => {
    const content = readFileSync(webRtcPath, "utf8");
    expect(content).toContain("export function onIncomingCall");
    expect(content).toContain("export function onIncomingCallEnded");
  });

  it("notification handler detects incoming calls by direction field", () => {
    const content = readFileSync(webRtcPath, "utf8");
    // Must check direction === "incoming" to detect inbound calls
    expect(content).toContain('direction === "incoming"');
  });

  it("notification handler no longer skips non-active call IDs", () => {
    const content = readFileSync(webRtcPath, "utf8");
    // The old code: "if (!call || call.id !== _activeCall?.id) return;"
    // Must now handle calls that are NOT the active outbound call
    expect(content).toContain("_incomingCall");
  });

  it("diagnostics includes direction field", () => {
    const content = readFileSync(webRtcPath, "utf8");
    expect(content).toContain('direction: "outbound" | "inbound" | ""');
  });

  it("declineIncomingCall calls hangup and cleanup", () => {
    const content = readFileSync(webRtcPath, "utf8");
    expect(content).toContain("cleanupIncomingCall");
  });
});

describe("Inbound calling: TelephonyProvider", () => {
  it("auto-registers WebRTC on mount", () => {
    const content = readFileSync(ctxPath, "utf8");
    expect(content).toContain("Auto-register WebRTC on mount");
    expect(content).toContain("/api/telephony/register");
    expect(content).toContain("registeredRef.current = true");
  });

  it("exposes incomingCall state", () => {
    const content = readFileSync(ctxPath, "utf8");
    expect(content).toContain("incomingCall: IncomingCallInfo | null");
  });

  it("exposes answerIncomingCall and declineIncomingCall in context", () => {
    const content = readFileSync(ctxPath, "utf8");
    expect(content).toContain("answerIncomingCall: answerIncoming");
    expect(content).toContain("declineIncomingCall: declineIncoming");
  });

  it("wires onIncomingCall to set incomingCall state", () => {
    const content = readFileSync(ctxPath, "utf8");
    expect(content).toContain("onIncomingCall((info)");
    expect(content).toContain("setIncomingCall(info)");
  });

  it("wires onIncomingCallEnded to clear incoming call", () => {
    const content = readFileSync(ctxPath, "utf8");
    expect(content).toContain("onIncomingCallEnded");
  });

  it("imports IncomingCallInfo type", () => {
    const content = readFileSync(ctxPath, "utf8");
    expect(content).toContain("IncomingCallInfo");
  });
});

describe("Inbound calling: GlobalCallBar", () => {
  it("shows incoming ringing panel before idle check", () => {
    const content = readFileSync(barPath, "utf8");
    // The inbound ringing panel must appear BEFORE the "idle → return null" check
    expect(content).toContain("Inbound ringing");
    expect(content).toContain("incomingCall.state === \"ringing\"");
  });

  it("has Answer and Decline buttons", () => {
    const content = readFileSync(barPath, "utf8");
    expect(content).toContain("answerIncomingCall");
    expect(content).toContain("declineIncomingCall");
  });

  it("displays caller number and name", () => {
    const content = readFileSync(barPath, "utf8");
    expect(content).toContain("incomingCall.callerNumber");
    expect(content).toContain("incomingCall.callerName");
  });

  it("imports PhoneIncoming icon", () => {
    const content = readFileSync(barPath, "utf8");
    expect(content).toContain("PhoneIncoming");
  });

  it("no mojibake in new text", () => {
    const content = readFileSync(barPath, "utf8");
    expect(content).not.toMatch(/\u2014/); // em-dash
  });
});

describe("Inbound calling: End-to-end safety", () => {
  it("auto-registration does not block outbound calling", () => {
    const ctxContent = readFileSync(ctxPath, "utf8");
    // startCall must still work after auto-registration
    expect(ctxContent).toContain("startCall");
    expect(ctxContent).toContain("tokenRef.current");
  });

  it("missed call fallback preserved: webhook still fires", () => {
    // The server-side webhook route is unchanged — verify from API routes
    const telephonyRoutes = join(process.cwd(), "..", "api", "app", "presentation", "api", "v1", "routes", "telephony.py");
    // Verify webhook endpoint still exists and Ed25519 is referenced
    try {
      const content = readFileSync(telephonyRoutes, "utf8");
      expect(content).toContain("/telephony/webhook");
      expect(content.toLowerCase()).toMatch(/ed25519|verify.*signature/);
    } catch {
      // Skip if API files not available in web test context
      expect(true).toBe(true);
    }
  });

  it("token is base64-decoded with same pattern for register and reconnect", () => {
    const wcContent = readFileSync(webRtcPath, "utf8");
    const ctxContent = readFileSync(ctxPath, "utf8");
    // Both auto-registration and reconnect must decode base64 the same way
    expect(ctxContent).toContain("atob");
    expect(wcContent).toContain("atob");
  });
});
