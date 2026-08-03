import { describe, expect, it } from "vitest";
import { buildToolPayload } from "@/lib/tool-submission";

describe("free-tool lead handoff", () => {
  it("maps a tool result into the durable CRM assessment contract", () => {
    const payload = buildToolPayload({
      requestId: "req-123",
      source_tool: "automation-roi-calculator",
      calculated_summary: "Estimated first-year ROI: 42%",
      name: "Vinicius Dias",
      email: "owner@example.com",
      company: "Example Co",
      contact_method: "Email",
      attribution: { utm_source: "google", landing_page: "/free-tools/automation-roi-calculator" },
    });

    expect(payload.source).toBe("free_tool");
    expect(payload.answers).toMatchObject({ source_tool: "automation-roi-calculator", calculated_summary: "Estimated first-year ROI: 42%" });
    expect(payload.contact).toMatchObject({ first_name: "Vinicius", last_name: "Dias", email: "owner@example.com" });
    expect(payload.company.name).toBe("Example Co");
    expect(payload.consent).toEqual({ privacy_accepted: true, marketing_accepted: false });
    expect(payload.attribution).toMatchObject({ utm_source: "google", landing_page: "/free-tools/automation-roi-calculator" });
  });

  it("keeps a one-word name valid for the CRM schema", () => {
    const payload = buildToolPayload({ source_tool: "crm-readiness-assessment", name: "Vini", email: "vini@example.com", company: "PNS" });
    expect(payload.contact.last_name).toBe("Not provided");
  });
});
