import { NextResponse } from "next/server";
import crypto from "crypto";
import { buildToolPayload } from "@/lib/tool-submission";

export const runtime = "nodejs";

// ── Helpers ──
function generateRequestId(): string {
  return `pns_${Date.now().toString(36)}_${crypto.randomBytes(6).toString("hex")}`;
}

function getCrmBaseUrl(): string | null {
  const raw = process.env.CRM_API_BASE_URL;
  if (!raw) return null;
  return raw.replace(/\/+$/, "");
}

async function checkCrmHealth(crmUrl: string): Promise<boolean> {
  try {
    const res = await fetch(`${crmUrl}/api/v1/health/live`, { signal: AbortSignal.timeout(5000) });
    return res.ok;
  } catch { return false; }
}

function buildPayload(body: Record<string, unknown>) {
  // Tool-style submission (from free-tools pages)
  if (body.source_tool || body.calculated_summary) {
    return buildToolPayload(body);
  }

  // Standard assessment submission
  const contactName = String(body.contactName || "");
  const nameParts = contactName.split(" ");
  return {
    assessment_version: "1.0",
    request_id: String(body.requestId || ""),
    answers: {
      businessType: String(body.businessType || ""),
      mainProblems: (body.mainProblems as string[]) || [],
      currentProcess: String(body.currentProcess || ""),
      weeklyTimeSpent: String(body.weeklyTimeSpent || ""),
      peopleInvolved: String(body.peopleInvolved || ""),
    },
    results: (body.results as Record<string, unknown>) || {},
    contact: {
      first_name: nameParts[0] || "",
      last_name: nameParts.slice(1).join(" ") || "",
      email: String(body.contactEmail || ""),
      phone: body.contactPhone ? String(body.contactPhone) : null,
      preferred_contact_method: String(body.preferredContactMethod || "email"),
      best_time_to_contact: body.bestTimeToContact ? String(body.bestTimeToContact) : null,
    },
    company: {
      name: String(body.contactCompany || ""),
      industry: String(body.businessType || "Other"),
      employee_range: body.peopleInvolved ? String(body.peopleInvolved) : null,
    },
    consent: { privacy_accepted: true, marketing_accepted: false },
  };
}

// ── Rate limiter (in-memory, per-Vercel-instance) ──
const RATE_WINDOW_MS = 60_000; // 1 minute
const MAX_REQUESTS_PER_WINDOW = 5;
const rateMap = new Map<string, { count: number; resetAt: number }>();

function checkRateLimit(ip: string): boolean {
  const now = Date.now();
  const entry = rateMap.get(ip);
  if (!entry || now > entry.resetAt) {
    rateMap.set(ip, { count: 1, resetAt: now + RATE_WINDOW_MS });
    return true;
  }
  if (entry.count >= MAX_REQUESTS_PER_WINDOW) return false;
  entry.count++;
  return true;
}

// ── Validation ──
const MAX_BODY_SIZE = 64_000; // 64 KB
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function extractIp(request: Request): string {
  return (
    request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ||
    request.headers.get("x-real-ip") ||
    "unknown"
  );
}

// ── POST: Submit assessment (Policy A — CRM-only intake) ──
export async function POST(request: Request) {
  const ip = extractIp(request);
  if (!checkRateLimit(ip)) {
    return NextResponse.json(
      { error: "Too many requests. Please wait a moment before trying again." },
      { status: 429 },
    );
  }

  // Check body size before parsing
  const contentLength = parseInt(request.headers.get("content-length") || "0", 10);
  if (contentLength > MAX_BODY_SIZE) {
    return NextResponse.json(
      { error: "Request too large. Please reduce the amount of data submitted." },
      { status: 413 },
    );
  }

  const crmUrl = getCrmBaseUrl();
  if (!crmUrl) {
    return NextResponse.json({ error: "Assessment submissions are temporarily unavailable.", retry: true, reason: "crm_not_configured" }, { status: 503 });
  }

  // Policy A: Verify CRM health before accepting payload
  const crmHealthy = await checkCrmHealth(crmUrl);
  if (!crmHealthy) {
    return NextResponse.json({ error: "We couldn't securely submit your assessment yet. Your answers remain saved on this device. Please try again.", retry: true, reason: "crm_unhealthy" }, { status: 503 });
  }

  try {
    const body = await request.json();

    // Accept both assessment-style (contactName/contactEmail) and tool-style (name/email)
    const effectiveName = String(body.contactName || body.name || "");
    const effectiveEmail = String(body.contactEmail || body.email || "");

    if (!effectiveEmail || !effectiveName) {
      return NextResponse.json({ error: "Name and email are required." }, { status: 400 });
    }

    // Server-side email validation
    if (!EMAIL_RE.test(effectiveEmail)) {
      return NextResponse.json({ error: "Please enter a valid email address." }, { status: 400 });
    }

    const requestId = generateRequestId();
    const payload = buildPayload({ ...body, requestId });

    try {
      const crmEndpoint = `${crmUrl}/api/v1/public/automation-assessment`;
      const crmRes = await fetch(crmEndpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Idempotency-Key": requestId },
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(15000),
      });

      const crmData = await crmRes.json().catch(() => ({}));

      // Policy A: Only 201 after CRM confirms durable persistence
      if (crmRes.ok) {
        return NextResponse.json({
          status: "persisted",
          requestId,
          submissionId: crmData.submission_id || crmData.assessment_id || null,
          message: "Assessment received. We are preparing your results.",
        }, { status: 201 });
      }

      console.error(`[assessment] CRM rejected ${requestId}: ${crmRes.status}`);
      return NextResponse.json({ error: "We couldn't process your assessment. Please review your responses and try again.", requestId, retry: true, reason: `crm_rejected_${crmRes.status}` }, { status: 502 });

    } catch (err) {
      console.error(`[assessment] CRM unreachable for ${requestId}: ${String(err)}`);
      return NextResponse.json({ error: "We couldn't securely submit your assessment yet. Your answers remain saved on this device. Please try again.", requestId, retry: true, reason: "crm_unreachable" }, { status: 503 });
    }
  } catch (error) {
    const msg = error instanceof Error ? error.message : "Unknown error";
    console.error(`[assessment] Unexpected error: ${msg}`);
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}

// ── PUT: Retry a previously-failed submission ──
export async function PUT(request: Request) {
  const ip = extractIp(request);
  if (!checkRateLimit(ip)) {
    return NextResponse.json(
      { error: "Too many requests. Please wait a moment before trying again." },
      { status: 429 },
    );
  }

  const crmUrl = getCrmBaseUrl();
  if (!crmUrl) {
    return NextResponse.json({ error: "Assessment submissions are temporarily unavailable.", retry: true, reason: "crm_not_configured" }, { status: 503 });
  }

  const crmHealthy = await checkCrmHealth(crmUrl);
  if (!crmHealthy) {
    return NextResponse.json({ error: "System still unavailable. Please try again in a moment.", retry: true, reason: "crm_unhealthy" }, { status: 503 });
  }

  try {
    const body = await request.json();
    const requestId = String(body.requestId || generateRequestId());
    const payload = buildPayload({ ...body, requestId });

    const crmEndpoint = `${crmUrl}/api/v1/public/automation-assessment`;
    const crmRes = await fetch(crmEndpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Idempotency-Key": requestId },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(15000),
    });

    const crmData = await crmRes.json().catch(() => ({}));

    if (crmRes.ok) {
      return NextResponse.json({ status: "persisted", requestId, submissionId: crmData.submission_id || crmData.assessment_id || null }, { status: 201 });
    }

    return NextResponse.json({ error: "Retry failed. Your form data is preserved. Please try again later.", requestId, retry: true, reason: "crm_rejected" }, { status: 503 });
  } catch (error) {
    const msg = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}

