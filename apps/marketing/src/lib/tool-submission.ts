export function buildToolPayload(body: Record<string, unknown>) {
  const nameParts = String(body.name || "").trim().split(/\s+/);
  const attribution = body.attribution && typeof body.attribution === "object"
    ? body.attribution as Record<string, unknown>
    : {};

  return {
    assessment_version: "tool-1.0",
    request_id: String(body.requestId || ""),
    source: "free_tool",
    answers: {
      source_tool: String(body.source_tool || "unknown"),
      calculated_summary: String(body.calculated_summary || ""),
      preferred_contact_method: String(body.contact_method || "Email"),
    },
    results: {},
    contact: {
      first_name: nameParts[0] || "",
      last_name: nameParts.slice(1).join(" ") || "Not provided",
      email: String(body.email || ""),
      phone: body.phone ? String(body.phone) : null,
      role: null,
    },
    company: { name: String(body.company || "Independent business"), industry: "Other", employee_range: null },
    consent: { privacy_accepted: true, marketing_accepted: false },
    attribution: {
      utm_source: attribution.utm_source ? String(attribution.utm_source) : null,
      utm_medium: attribution.utm_medium ? String(attribution.utm_medium) : null,
      utm_campaign: attribution.utm_campaign ? String(attribution.utm_campaign) : null,
      utm_term: attribution.utm_term ? String(attribution.utm_term) : null,
      utm_content: attribution.utm_content ? String(attribution.utm_content) : null,
      referrer: attribution.referrer ? String(attribution.referrer) : null,
      landing_page: attribution.landing_page ? String(attribution.landing_page) : null,
    },
  };
}
