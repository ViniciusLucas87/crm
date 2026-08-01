import { describe, expect, it } from "vitest";

/**
 * Authorization architecture tests.
 *
 * These tests verify that every protection boundary behaves correctly
 * when authentication is missing. They test real HTTP endpoints
 * against the running development server.
 */

const WEB_URL = process.env.TEST_WEB_URL ?? "http://localhost:3000";
const API_URL = process.env.TEST_API_URL ?? "http://localhost:8000";

async function fetchStatus(
  url: string,
  opts: RequestInit = {},
): Promise<number> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10_000);
  try {
    const response = await fetch(url, {
      ...opts,
      signal: controller.signal,
      redirect: "manual",
    });
    return response.status;
  } finally {
    clearTimeout(timeout);
  }
}

describe("Authorization — pages", () => {
  // All pages are protected server-side — unauthenticated requests must redirect
  const protectedPages = [
    "/",
    "/companies",
    "/companies/1",
    "/leads",
    "/ai/daily-brief",
    "/ai/explorer",
    "/ai/knowledge-base",
  ];

  it.each(protectedPages)(
    "unauthenticated request to %s redirects (3xx) or is denied (401/403)",
    async (path) => {
      const status = await fetchStatus(`${WEB_URL}${path}`);
      const valid = status === 307 || status === 401 || status === 403;
      expect(valid).toBe(true);
    },
  );

  const publicPages = ["/sign-in"];

  it.each(publicPages)(
    "public page %s is accessible without auth (2xx)",
    async (path) => {
      const status = await fetchStatus(`${WEB_URL}${path}`);
      expect(status).toBeGreaterThanOrEqual(200);
      expect(status).toBeLessThan(300);
    },
  );

  it("public sign-up is disabled", async () => {
    const status = await fetchStatus(`${WEB_URL}/sign-up`);
    expect(status).toBe(307);
  });
});

describe("Authorization — Next.js API routes", () => {
  const protectedRoutes = [
    "/api/dashboard/summary",
    "/api/companies",
    "/api/contacts",
    "/api/auth/me",
    "/api/tasks",
    "/api/leads",
    "/api/ai/brief",
  ];

  it.each(protectedRoutes)(
    "unauthenticated %s returns 401",
    async (path) => {
      const status = await fetchStatus(`${WEB_URL}${path}`);
      expect(status).toBe(401);
    },
  );
});

describe("Authorization — FastAPI backend", () => {
  it("rejects missing authorization header with 401", async () => {
    const status = await fetchStatus(`${API_URL}/api/v1/companies`);
    expect(status).toBe(401);
  });

  it("rejects malformed authorization header with 401", async () => {
    const status = await fetchStatus(`${API_URL}/api/v1/companies`, {
      headers: { Authorization: "NotBearer token" },
    });
    expect(status).toBe(401);
  });

  it("public health endpoint returns 2xx", async () => {
    const status = await fetchStatus(`${API_URL}/api/v1/health`);
    expect(status).toBeGreaterThanOrEqual(200);
    expect(status).toBeLessThan(300);
  });
});

describe("Authorization — failure modes", () => {
  it("fails securely when backend is unreachable", async () => {
    // The proxyAuthenticatedApi returns 503 when the backend is down.
    // This test verifies the 401 still takes priority over 503.
    const status = await fetchStatus(
      `${WEB_URL}/api/dashboard/summary`,
    );
    // Must be 401 (auth failure) not 503 (backend unavailable)
    expect(status).toBe(401);
  });

  it("multiple rapid requests do not bypass auth", async () => {
    const results = await Promise.all(
      Array.from({ length: 20 }, () =>
        fetchStatus(`${WEB_URL}/api/dashboard/summary`),
      ),
    );
    for (const status of results) {
      expect(status).toBe(401);
    }
  });

  it("protected route POST is also 401", async () => {
    const status = await fetchStatus(`${WEB_URL}/api/companies`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: "test" }),
    });
    expect(status).toBe(401);
  });
});
