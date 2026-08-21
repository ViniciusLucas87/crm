import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";

import CallCenterScreen from "@/components/call-center/call-center-screen";

const startCall = vi.fn();

vi.mock("@/lib/telephony-context", () => ({
  useTelephony: () => ({
    call: { state: "idle", duration: 0 },
    startCall,
    transcription: { segments: [] },
    transcriptId: null,
  }),
}));

const emptyHistory = {
  phone_number: "+16042251745",
  items: [],
  total: 0,
};

const connectedCallHistory = {
  phone_number: "+16042251745",
  total: 1,
  items: [{
    id: "call-1",
    kind: "call" as const,
    direction: "outbound" as const,
    status: "connected",
    phone_number: "+16045550123",
    timestamp: "2026-08-21T18:43:00Z",
    duration_seconds: 45,
    preview: "Outgoing call",
  }],
};

describe("CallCenterScreen", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/calls/browser")) {
        return new Response(JSON.stringify({ id: 91 }), { status: 200 });
      }
      return new Response(JSON.stringify(emptyHistory), { status: 200 });
    }));
  });

  it("shows the business line and collapsible script", async () => {
    const user = userEvent.setup();
    render(<CallCenterScreen />);

    expect(await screen.findByText("(604) 225 1745")).toBeTruthy();
    expect(screen.getByText(/Did I catch you at an okay time/)).toBeTruthy();
    await user.click(screen.getByRole("button", { name: /Simple PNS call script/i }));
    expect(screen.queryByText(/Did I catch you at an okay time/)).toBeNull();
  });

  it("starts a call to a number entered by the user", async () => {
    const user = userEvent.setup();
    render(<CallCenterScreen />);

    await user.type(screen.getByLabelText("Phone number"), "6045550123");
    await user.click(screen.getByRole("button", { name: "Call this number" }));

    await waitFor(() => {
      expect(startCall).toHaveBeenCalledWith(0, "+16045550123", "", "", 91);
    });
  });

  it("previews the Never Miss follow-up after selecting a connected outbound call", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/calls/browser")) return new Response(JSON.stringify({ id: 91 }), { status: 200 });
      return new Response(JSON.stringify(connectedCallHistory), { status: 200 });
    }));

    render(<CallCenterScreen />);
    await user.click(await screen.findByRole("button", { name: /Outgoing call outbound/i }));

    expect(await screen.findByRole("heading", { name: "Send Never Miss details" })).toBeTruthy();
    expect((screen.getByRole("textbox", { name: "Never Miss follow-up message" }) as HTMLTextAreaElement).value).toContain("30-day free trial");
    await user.click(screen.getByRole("button", { name: "Send Never Miss details" }));
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith("/api/telephony/sms", expect.objectContaining({ method: "POST" }));
    });
  });
});
